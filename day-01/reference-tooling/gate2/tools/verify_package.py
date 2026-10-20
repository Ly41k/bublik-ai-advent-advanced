"""Verify frozen inputs and original baseline bytes without changing them."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    manifest = json.loads((ROOT / "gate2/frozen-manifest.json").read_text())
    failures: list[str] = []
    for name, expected in manifest["files"].items():
        path = ROOT / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(name)
    baseline = ROOT / "weeks/week-01/evidence/day-01/baseline-core.sha256"
    for line in baseline.read_text().splitlines():
        expected, name = line.split("  ", 1)
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            failures.append("BASELINE:" + name)
    print(json.dumps({"status": "FAIL" if failures else "PASS", "failures": failures}))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
