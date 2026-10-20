"""Verify this exported package without models, installs, or rewriting files."""

import hashlib
import json
from pathlib import Path


def main() -> int:
    """Check regular file bytes and path containment against the delivery manifest."""
    root = Path(__file__).resolve().parent
    try:
        data = json.loads((root / "DELIVERY-SHA256.json").read_bytes())
        required = {
            "README_RU.md",
            "app/AGENTS.md",
            "app/pyproject.toml",
            "control/protected-inputs.json",
            "proof/final-status.json",
        }
        if not isinstance(data, dict) or not required.issubset(data):
            raise ValueError("INCOMPLETE_DELIVERY_MANIFEST")
        for name, expected in data.items():
            part = Path(name)
            target = root / part
            if (
                part.is_absolute()
                or ".." in part.parts
                or not target.is_file()
                or any(parent.is_symlink() for parent in (target, *target.parents))
                or not target.resolve().is_relative_to(root)
                or hashlib.sha256(target.read_bytes()).hexdigest() != expected
            ):
                raise ValueError("DELIVERY_INTEGRITY_MISMATCH")
    except (ValueError, KeyError, TypeError, OSError):
        print('{"status":"BLOCKED","error_code":"DELIVERY_INTEGRITY_MISMATCH"}')
        return 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "files_verified": len(data),
                "scope": "delivery_integrity_only",
                "codex_invocations": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
