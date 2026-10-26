"""Capture a single immutable pytest attempt, including generated inputs."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("tests", nargs="+")
    args = parser.parse_args()
    app = args.app.resolve()
    run = args.run_dir.resolve()
    run.mkdir(parents=True, exist_ok=False)  # first-run evidence must never be overwritten
    command = [sys.executable, "-m", "pytest", "-vv", "--junitxml=" + str(run / "junit.xml"), *args.tests]
    inputs = {}
    for name in args.tests:
        data = (app / name).read_bytes()
        inputs[name] = hashlib.sha256(data).hexdigest()
        target = run / "generation" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(app / name, target)
    sources = {str(p.relative_to(app)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted((app / "src").rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    report = {"started_utc": datetime.now(timezone.utc).isoformat(), "command": command,
              "cwd": "day-03/app", "environment": {"PYTHONPATH": "src"},
              "generated_test_sha256": inputs, "production_sha256": sources,
              "status": "RUNNING", "exit_code": None}
    (run / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    result = subprocess.run(command, cwd=app, env={**os.environ, "PYTHONPATH": str(app / "src")},
                            capture_output=True, text=True)
    (run / "stdout.txt").write_text(result.stdout)
    (run / "stderr.txt").write_text(result.stderr)
    report.update(status="PASS" if result.returncode == 0 else "FAIL", exit_code=result.returncode,
                  finished_utc=datetime.now(timezone.utc).isoformat())
    (run / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
