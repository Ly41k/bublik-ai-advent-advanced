"""Run the fixed offline quality gate and preserve actual subprocess results."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import shlex
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    ("compile", ("-m", "compileall", "-q", "src", "tests", "scripts")),
    ("import", ("-c", "from bublik.main import create_app; create_app()")),
    ("ruff_lint", ("-m", "ruff", "check", ".")),
    ("ruff_format", ("-m", "ruff", "format", "--check", ".")),
    ("pytest", ("-m", "pytest", "-q")),
)


def sanitize(text: str) -> str:
    """Remove machine-specific paths without changing check outcomes."""
    substitutions = sorted(
        ((str(ROOT), "<REPO>"), (sys.prefix, "<VENV>"), (str(Path.home()), "<HOME>")),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    for original, replacement in substitutions:
        text = text.replace(original, replacement)
    return text


def source_manifest() -> dict[str, str]:
    """Hash experiment-relevant files; ignore logs, caches and local state."""
    paths = [ROOT / name for name in ("pyproject.toml", "requirements.lock", "uv.lock")]
    for folder in ("src", "tests", "scripts"):
        paths.extend(sorted((ROOT / folder).rglob("*.py")))
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def main() -> int:
    """Write an auditable report and return the combined status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    permitted = (ROOT / "local-evidence", ROOT / "weeks/week-01/evidence/day-01")
    if not any(output.is_relative_to(folder) for folder in permitted):
        parser.error("--output must be inside a designated evidence directory")
    if output.exists():
        parser.error("report already exists; use a new filename to preserve evidence")
    output.parent.mkdir(parents=True, exist_ok=True)
    packages = {
        distribution.metadata["Name"]: distribution.version
        for distribution in importlib.metadata.distributions()
    }
    report = [
        "Bublik baseline quality gate",
        f"timestamp_utc: {datetime.now(UTC).isoformat()}",
        f"execution_os: {platform.system()} {platform.machine()}",
        f"python: {platform.python_version()}",
        "codex_invocations: 0",
        "checks_require_external_network: false",
        "packages: " + json.dumps(packages, sort_keys=True),
        "source_manifest_sha256: " + json.dumps(source_manifest(), sort_keys=True),
    ]
    failed = False
    for label, arguments in COMMANDS:
        command = [sys.executable, *arguments]
        started = time.monotonic()
        try:
            result = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, timeout=120, check=False
            )
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            code, stdout, stderr = 124, str(error.stdout or ""), str(error.stderr or "")
        duration = time.monotonic() - started
        failed = failed or code != 0
        report.extend(
            (
                f"\n[{label}]",
                "command: python " + shlex.join(arguments),
                f"exit_code: {code}",
                f"duration_seconds: {duration:.3f}",
                "stdout:\n" + stdout,
                "stderr:\n" + stderr,
            )
        )
        print(f"{label}: {'PASS' if code == 0 else 'FAIL'} (exit {code})", flush=True)
    report.append("\noverall: " + ("FAIL" if failed else "PASS"))
    output.write_text(sanitize("\n".join(report)) + "\n", encoding="utf-8")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
