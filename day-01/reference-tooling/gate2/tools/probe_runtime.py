"""Probe the real installed Codex configuration without starting a model turn."""

import argparse
import hashlib
import json
import os
import platform
import queue
import shutil
import subprocess
import threading
from pathlib import Path
from typing import TextIO

ROOT = Path(__file__).resolve().parents[2]


def digest(path: Path) -> str:
    """Hash bytes without exposing file content."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def redact(text: str) -> str:
    """Keep machine paths out of shareable reports."""
    return text.replace(str(ROOT), "<REPO>").replace(str(Path.home()), "<HOME>")


class LocalRpc:
    """Small stdio client for config/skill reads; never sends turn/start."""

    def __init__(self, codex: str) -> None:
        self.process = subprocess.Popen(
            [codex, "app-server", "--strict-config", "-c", 'model_provider="openai"'],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self.messages: queue.Queue[dict[str, object] | None] = queue.Queue()
        self.sequence = 0
        assert self.process.stdout is not None
        threading.Thread(target=self._read, args=(self.process.stdout,), daemon=True).start()
        try:
            self.request(
                "initialize",
                {"clientInfo": {"name": "bublik_gate2_probe", "version": "1.0"}},
            )
            self.send({"method": "initialized", "params": {}})
        except Exception:
            self.close()
            raise

    def _read(self, stream: TextIO) -> None:
        for line in stream:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                self.messages.put(value)
        self.messages.put(None)

    def send(self, message: dict[str, object]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(self, method: str, parameters: dict[str, object]) -> dict[str, object]:
        self.sequence += 1
        self.send({"id": self.sequence, "method": method, "params": parameters})
        while True:
            message = self.messages.get(timeout=30)
            if message is None:
                raise RuntimeError("Codex app-server closed before its response")
            if message.get("id") != self.sequence:
                continue
            if "error" in message:
                raise RuntimeError(redact(json.dumps(message["error"])))
            result = message.get("result")
            if not isinstance(result, dict):
                raise TypeError(f"Unexpected {method} result")
            return result

    def close(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)


def objects(value: object) -> list[dict[str, object]]:
    """Traverse RPC data without relying on undocumented nesting."""
    if isinstance(value, dict):
        result = [value]
        for child in value.values():
            result.extend(objects(child))
        return result
    if isinstance(value, list):
        return [entry for child in value for entry in objects(child)]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", default=shutil.which("codex"))
    parser.add_argument("--install-global", action="store_true")
    parser.add_argument("--offline", action="store_true", help="Config-only; auth not required")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.codex:
        parser.error("Codex CLI is not on PATH")
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "local-evidence"):
        parser.error("--output must be under local-evidence/")
    if output.exists():
        parser.error("output already exists; preserve earlier evidence")
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    global_rules = home / "AGENTS.md"
    override = home / "AGENTS.override.md"
    template = ROOT / "gate2/GLOBAL_AGENTS_V1.md"
    if args.install_global:
        if override.exists() or override.is_symlink():
            parser.error("existing AGENTS.override.md requires local review; nothing overwritten")
        if global_rules.is_symlink():
            parser.error("existing global instructions symlink requires local review")
        if global_rules.exists() and global_rules.read_bytes() != template.read_bytes():
            parser.error("existing global AGENTS.md requires review; nothing overwritten")
        home.mkdir(parents=True, exist_ok=True)
        if not global_rules.exists():
            with global_rules.open("xb") as stream:
                stream.write(template.read_bytes())
    version = subprocess.run(
        [args.codex, "--version"], capture_output=True, text=True, check=False, timeout=15
    )
    login = subprocess.run(
        [args.codex, "login", "status"], capture_output=True, text=True, check=False, timeout=15
    )
    report: dict[str, object] = {
        "os": platform.system(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "codex_version": version.stdout.strip(),
        "auth_chatgpt": login.returncode == 0
        and "Logged in using ChatGPT" in login.stdout + login.stderr,
        "model_turns_started": 0,
        "global_rules_exact_template": global_rules.is_file()
        and not override.exists()
        and global_rules.read_bytes() == template.read_bytes(),
        "global_rules_sha256": digest(global_rules) if global_rules.is_file() else None,
        "user_runtime_config_sha256": digest(home / "config.toml")
        if (home / "config.toml").is_file()
        else None,
    }
    rpc = None
    try:
        rpc = LocalRpc(args.codex)
        config_result = rpc.request("config/read", {"cwd": str(ROOT), "includeLayers": True})
        skill_result = rpc.request("skills/list", {"cwds": [str(ROOT)], "forceReload": True})
        config = config_result.get("config", {})
        if not isinstance(config, dict):
            raise TypeError("Effective config must be an object")
        keys = (
            "model",
            "model_provider",
            "model_reasoning_effort",
            "approval_policy",
            "sandbox_mode",
            "web_search",
        )
        effective = {key: config.get(key) for key in keys}
        effective["agents"] = config.get("agents")
        effective["memories"] = config.get("memories")
        report["effective_settings"] = effective
        skills = [entry for entry in objects(skill_result) if entry.get("name") == "quality-gate"]
        expected = str(ROOT / ".agents/skills/quality-gate/SKILL.md")
        report["project_skill_discovered"] = any(
            str(entry.get("path")) == expected for entry in skills
        )
        report["skill_errors"] = [
            entry["errors"] for entry in objects(skill_result) if entry.get("errors")
        ]
        wanted = json.loads((ROOT / "gate2/experiment-settings.json").read_text())
        report["effective_settings_match"] = (
            all(
                effective[key] == wanted[key]
                for key in (
                    "model",
                    "model_provider",
                    "model_reasoning_effort",
                    "approval_policy",
                    "web_search",
                )
            )
            and effective["sandbox_mode"] == wanted["sandbox_mode_generation"]
        )
        agents = config.get("agents")
        report["agent_settings_match"] = (
            isinstance(agents, dict)
            and agents.get("enabled") is True
            and agents.get("max_concurrent_threads_per_session") == 1
        )
        memories = config.get("memories")
        report["memory_settings_match"] = (
            isinstance(memories, dict)
            and memories.get("use_memories") is False
            and memories.get("generate_memories") is False
        )
        report["agent_discovery"] = "NOT_PROVEN_UNTIL_NATIVE_SPAWN"
        report["status"] = "OFFLINE_CONFIG_PASS" if args.offline else "PREFLIGHT_PASS"
        if (
            version.stdout.strip() != "codex-cli 0.163.0"
            or platform.python_version() != "3.13.3"
            or not report["global_rules_exact_template"]
            or not report["effective_settings_match"]
            or not report["agent_settings_match"]
            or not report["memory_settings_match"]
            or not report["project_skill_discovered"]
            or report["skill_errors"]
            or (not args.offline and not report["auth_chatgpt"])
        ):
            report["status"] = "BLOCKED"
    except (OSError, RuntimeError, TypeError, queue.Empty) as error:
        report["status"] = "BLOCKED"
        report["error"] = redact(str(error))
    finally:
        if rpc is not None:
            rpc.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(redact(json.dumps(report, indent=2)) + "\n", encoding="utf-8")
    print(report["status"])
    return int(report["status"] == "BLOCKED")


if __name__ == "__main__":
    raise SystemExit(main())
