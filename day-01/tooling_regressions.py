"""Run retained E1/native/contract tests only; never call Codex or native sessions."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    """Return nonzero if any pinned offline regression suite fails."""
    original = ROOT / "reference-tooling"
    suites = (
        (
            "native_trace_v203",
            [
                "-m",
                "unittest",
                "discover",
                "-s",
                "gate2/diagnostic-fixes/native-trace-v2.0.3",
                "-p",
                "test_*.py",
            ],
        ),
        (
            "e1",
            [
                "-m",
                "unittest",
                "discover",
                "-s",
                "gate3/evaluation-fixes/acceptance-root-v1.0.0",
                "-p",
                "test_*.py",
            ],
        ),
        (
            "agent_contracts",
            [
                "-m",
                "pytest",
                "-q",
                "-o",
                "addopts=",
                "gate2/tool_tests/test_protocol_validation.py",
            ],
        ),
    )
    results = []
    for name, args in suites:
        command = [sys.executable, "-B", *args]
        result = subprocess.run(
            command, cwd=original, capture_output=True, text=True, timeout=120, check=False
        )
        results.append(
            {
                "name": name,
                "command": command,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
    passed = all(item["exit_code"] == 0 for item in results)
    print(
        json.dumps(
            {
                "status": "PASS" if passed else "FAIL",
                "suites": results,
                "codex_invocations": 0,
                "model_calls": 0,
            },
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
