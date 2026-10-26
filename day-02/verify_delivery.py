"""Read-only integrity and targeted privacy checks. No app or native imports."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    manifest_path = ROOT / "SHA256.json"
    manifest = json.loads(manifest_path.read_bytes())
    observed = {}
    findings = []
    patterns = {
        "machine_home": "/" + "Users" + "/",
        "machine_workspace": "/" + "workspace" + "/",
        "private_temp": r"/(?:private/)?var/" + "folders" + "/",
        "runtime_temp": r"/(?:private/)?tmp/" + "bublik",
        "history_control_marker": "BUBLIK_" + r"(?:DAY2|GATE3)_[A-Za-z0-9]+",
        "jwt": r"eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}",
        "api_token": r"\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b",
        "aws_key": r"\bAKIA[A-Z0-9]{16}\b",
        "private_key": "BEGIN " + r"[A-Z ]*PRIVATE KEY",
        "bearer_value": r"(?i)bearer[ \t]+[A-Za-z0-9._-]{24,}",
        "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    }
    for path in sorted(ROOT.rglob("*")):
        if path.is_symlink():
            raise ValueError("SYMLINK_FORBIDDEN")
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        if path != manifest_path:
            observed[rel] = hashlib.sha256(data).hexdigest()
        if path.name in {"auth.json", ".env"} or path.suffix in {
            ".sqlite",
            ".db",
            ".zip",
            ".png",
            ".jpg",
            ".jsonl",
        }:
            findings.append({"path": rel, "kind": "PRIVATE_OR_BINARY_EXPORT"})
        text = data.decode("utf-8")
        for name, expression in patterns.items():
            if re.search(expression, text):
                findings.append({"path": rel, "kind": name})
    if observed != manifest:
        raise ValueError("MANIFEST_SET_OR_SHA_MISMATCH")
    if findings:
        print(json.dumps({"status": "BLOCKED", "findings": findings}, indent=2))
        raise SystemExit(1)
    print(
        json.dumps(
            {
                "status": "PASS_CANDIDATE_INTEGRITY_AND_TARGETED_PRIVACY_ONLY",
                "manifest_entries": len(manifest),
                "privacy_findings": 0,
                "new_model_turns": 0,
                "native_execution": "NOT_RUN",
                "course_minimum": "PARTIAL_BLOCKED",
                "limitation": "Targeted scan and explicit export allowlist; not full private-journal verification.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
