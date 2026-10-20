"""Run only the four explicit Gate 2 probes, never the control prompt."""

import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

from probe_runtime import ROOT, digest, redact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Actually invoke Codex models")
    parser.add_argument(
        "--step", choices=("instructions", "skill", "agent_missing", "agent_success"), required=True
    )
    args = parser.parse_args()
    if not args.run:
        parser.error("--run is required; this command invokes a real Codex diagnostic")
    if platform.python_version() != "3.13.3" or platform.system() != "Darwin":
        parser.error("Live Gate 2 diagnostics are intended for the confirmed Mac Python 3.13.3")
    codex = shutil.which("codex")
    if not codex:
        parser.error("Codex is not installed")
    version = subprocess.check_output([codex, "--version"], text=True).strip()
    if version != "codex-cli 0.163.0":
        parser.error("Codex must remain 0.163.0")
    preflight = ROOT / "local-evidence/gate2/mac-runtime-probe.json"
    if not preflight.is_file():
        parser.error("Run and review the Mac runtime preflight first")
    preflight_data = json.loads(preflight.read_text())
    if preflight_data.get("status") != "PREFLIGHT_PASS":
        parser.error("Mac runtime preflight has not passed")
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    if digest(home / "AGENTS.md") != preflight_data["global_rules_sha256"]:
        parser.error("Global rules changed after preflight")
    actual_config_hash = digest(home / "config.toml") if (home / "config.toml").is_file() else None
    if actual_config_hash != preflight_data["user_runtime_config_sha256"]:
        parser.error("User runtime config changed after preflight; rerun preflight")
    subprocess.run([str(ROOT / ".venv/bin/python"), "gate2/tools/verify_package.py"], check=True)
    manifest_path = ROOT / "gate2/frozen-manifest.json"
    manifest_hash = digest(manifest_path)
    expected_files = json.loads(manifest_path.read_text())["files"]
    source_inventory = {
        str(path) for folder in ("src", "tests") for path in (ROOT / folder).rglob("*.py")
    }
    directory = ROOT / "local-evidence/gate2" / args.step
    directory.mkdir(parents=True, exist_ok=False)
    prompt_path = ROOT / "gate2/diagnostics" / f"{args.step}.txt"
    prompt = prompt_path.read_text().replace("__REPO_ROOT__", str(ROOT))
    sandbox = "workspace-write" if args.step == "skill" else "read-only"
    command = [
        codex,
        "exec",
        "--strict-config",
        "-c",
        'model_provider="openai"',
        "--json",
        "--color",
        "never",
        "--sandbox",
        sandbox,
        "--output-last-message",
        str(directory / "result.json"),
        "-",
    ]
    metadata: dict[str, object] = {
        "step": args.step,
        "codex": version,
        "python": platform.python_version(),
        "os": platform.system(),
        "template_sha256": digest(prompt_path),
        "sandbox": sandbox,
        "command": command,
        "generation_invocations": 0,
        "diagnostic_parent_invocations": 1,
    }
    print(
        f"Running Gate 2 diagnostic: {args.step}. No control prompt will be executed.", flush=True
    )
    try:
        with (
            (directory / "events.jsonl").open("x") as stdout,
            (directory / "stderr.txt").open("x") as stderr,
        ):
            result = subprocess.run(
                command,
                cwd=ROOT,
                input=prompt,
                text=True,
                stdout=stdout,
                stderr=stderr,
                check=False,
            )
        metadata["exit_code"] = result.returncode
    finally:
        (directory / "metadata.json").write_text(redact(json.dumps(metadata, indent=2)) + "\n")
    changed = [name for name, expected in expected_files.items() if digest(ROOT / name) != expected]
    current_inventory = {
        str(path) for folder in ("src", "tests") for path in (ROOT / folder).rglob("*.py")
    }
    intact = (
        not changed
        and digest(manifest_path) == manifest_hash
        and current_inventory == source_inventory
    )
    (directory / "host-integrity.json").write_text(
        json.dumps({"status": "PASS" if intact else "FAIL", "changed_files": changed}) + "\n"
    )
    return result.returncode or int(not intact)


if __name__ == "__main__":
    raise SystemExit(main())
