"""Run the foundation gate with real subprocesses and pinned protected inputs."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    """Hash regular inputs; linked inputs are never accepted."""
    if not path.is_file() or path.is_symlink():
        raise ValueError("MISSING_OR_LINKED_PROTECTED_INPUT")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_protected(manifest: Path, expected_sha: str) -> None:
    """Compare bytes and source inventory with an externally pinned manifest."""
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha) or digest(manifest) != expected_sha:
        raise ValueError("PROTECTED_MANIFEST_CHANGED")
    inputs = json.loads(manifest.read_bytes())
    files = inputs["files"]
    if not isinstance(files, dict) or not files:
        raise ValueError("EMPTY_PROTECTED_MANIFEST")
    for name, expected in files.items():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ValueError("UNSAFE_PROTECTED_PATH")
        target = ROOT.parent / path
        if any(parent.is_symlink() for parent in (target, *target.parents)):
            raise ValueError("LINKED_PROTECTED_PATH")
        if digest(target) != expected:
            raise ValueError("PROTECTED_INPUT_CHANGED:" + name)
    folders = ("app/src", "app/tests", "app/scripts", "reference-tooling")
    actual = {
        path.relative_to(ROOT.parent).as_posix()
        for folder in folders
        for path in (ROOT.parent / folder).rglob("*.py")
    }
    expected = {
        name
        for name in files
        if name.endswith(".py")
        and name.startswith(("app/src/", "app/tests/", "app/scripts/", "reference-tooling/"))
    }
    if actual != expected:
        raise ValueError("PROTECTED_SOURCE_INVENTORY_CHANGED")


def commands() -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Use Ruff ANN for all functions and E1 boundaries for acceptance."""
    acceptance = ROOT.parent / "control/acceptance"
    return (
        ("compile", ("-m", "compileall", "-q", "src", "tests", "scripts")),
        ("import", ("-c", "from bublik.main import create_app; create_app()")),
        (
            "ruff_lint_and_annotations",
            ("-m", "ruff", "check", ".", "../tooling_regressions.py", "../verify_delivery.py"),
        ),
        (
            "ruff_format",
            (
                "-m",
                "ruff",
                "format",
                "--check",
                ".",
                "../tooling_regressions.py",
                "../verify_delivery.py",
            ),
        ),
        ("pytest_including_architecture_and_gate_regressions", ("-m", "pytest", "-q")),
        (
            "external_acceptance_e1",
            (
                "-m",
                "pytest",
                "-vv",
                "-c",
                str(ROOT / "pyproject.toml"),
                "--rootdir",
                str(acceptance),
                "--confcutdir",
                str(acceptance),
                "-p",
                "no:cacheprovider",
                "-o",
                "addopts=--strict-config --strict-markers",
                str(acceptance / "test_status_contract.py"),
            ),
        ),
        ("tooling_regressions", (str(ROOT.parent / "tooling_regressions.py"),)),
    )


def acceptance_ok(code: int, stdout: str) -> bool:
    """Require seventeen distinct executed cases, not a summary alone."""
    cases = re.findall(r"^(\S+::\S+) PASSED", stdout, re.MULTILINE)
    return (
        code == 0
        and len(cases) == len(set(cases)) == 17
        and bool(re.search(r"\b17 passed\b", stdout))
    )


def sanitize(value: str) -> str:
    """Remove local prefixes from shareable reports."""
    replacements = [
        (str(ROOT), "<APP>"),
        (sys.prefix, "<VENV>"),
        (str(ROOT.parent), "<PACKAGE>"),
        (str(Path.home()), "<HOME>"),
    ]
    for source, target in sorted(replacements, key=lambda item: -len(item[0])):
        value = value.replace(source, target)
    return value


def main(argv: list[str] | None = None) -> int:
    """Fail closed on mandatory failures and preserve existing reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--protected-manifest", type=Path, default=ROOT.parent / "control/protected-inputs.json"
    )
    parser.add_argument("--protected-sha256")
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if not output.resolve().is_relative_to(ROOT / "local-evidence") or output.is_symlink():
        parser.error("output must be inside app/local-evidence")
    if output.exists():
        parser.error("report exists: choose a new report name")
    report: dict[str, object] = {
        "gate": "BublikFoundationQualityGateV1",
        "status": "BLOCKED",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "environment": {
            "os": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "tool_versions": {
            name: importlib.metadata.version(name)
            for name in ("ruff", "pytest", "fastapi", "pydantic", "bublik-task-service")
        },
        "protected_manifest_sha256": args.protected_sha256,
        "codex_invocations": 0,
        "model_calls": 0,
        "checks": [],
        "architecture_check": "tests/test_architecture.py via mandatory pytest",
        "annotations_check": "Ruff ANN; no tests ANN201 exemption",
    }
    checks: list[dict[str, object]] = []
    report["checks"] = checks
    try:
        trusted_sha = args.protected_sha256
        if trusted_sha is None:
            trusted_sha = args.protected_manifest.with_suffix(".sha256").read_text().strip()
        report["protected_manifest_sha256"] = trusted_sha
        verify_protected(args.protected_manifest, trusted_sha)
        report["protected_before"] = "PASS"
        for label, arguments in commands():
            started = time.monotonic()
            try:
                result = subprocess.run(
                    [sys.executable, *arguments],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                code, stdout, stderr = result.returncode, result.stdout, result.stderr
            except (OSError, subprocess.TimeoutExpired) as error:
                code, stdout, stderr = 124, "", type(error).__name__
            ok = acceptance_ok(code, stdout) if label == "external_acceptance_e1" else code == 0
            checks.append(
                {
                    "name": label,
                    "command": [sys.executable, *arguments],
                    "exit_code": code,
                    "status": "PASS" if ok else "FAIL",
                    "stdout": stdout,
                    "stderr": stderr,
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
            )
            print(f"{label}: {'PASS' if ok else 'FAIL'} (exit {code})", flush=True)
        verify_protected(args.protected_manifest, trusted_sha)
        report["protected_after"] = "PASS"
        report["status"] = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    except (ValueError, KeyError, TypeError, OSError) as error:
        report["error_code"] = str(error) if isinstance(error, ValueError) else type(error).__name__
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(sanitize(json.dumps(report, ensure_ascii=False, indent=2)) + "\n")
    print("overall: " + str(report["status"]), flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
