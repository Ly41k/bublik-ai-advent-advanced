"""Verify delivered hashes and evidence consistency without rerunning tests."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"__pycache__", ".pytest_cache", ".ruff_cache", "node_modules", ".venv"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((ROOT / "SHA256_MANIFEST.json").read_text())
    actual = {str(p.relative_to(ROOT)): digest(p) for p in ROOT.rglob("*")
              if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP)
              and p.name != "SHA256_MANIFEST.json"}
    if actual != manifest["files"]:
        missing = set(manifest["files"]) - set(actual)
        extra = set(actual) - set(manifest["files"])
        changed = [p for p in actual.keys() & manifest["files"].keys()
                   if actual[p] != manifest["files"][p]]
        raise ValueError(f"MANIFEST_MISMATCH missing={missing} extra={extra} changed={changed}")
    first = json.loads((ROOT / "evidence/code/first-run/result.json").read_text())
    for relative, expected in first["generated_test_sha256"].items():
        if digest(ROOT / "app" / relative) != expected:
            raise ValueError(f"GENERATED_TEST_CHANGED: {relative}")
        if digest(ROOT / "evidence/code/first-run/generation" / relative) != expected:
            raise ValueError(f"GENERATION_SNAPSHOT_CHANGED: {relative}")
    for relative, expected in first["production_sha256"].items():
        path = ROOT / "app" / relative
        if relative == "src/bublik/main.py":
            path = ROOT / "evidence/code/production-at-first-run" / relative
        if digest(path) != expected:
            raise ValueError(f"FIRST_RUN_PRODUCTION_MISMATCH: {relative}")
    report = json.loads((ROOT / "REPORT.json").read_text())
    if first["exit_code"] != report["code_testing"]["first_exit_code"]:
        raise ValueError("FIRST_EXIT_CODE_MISMATCH")
    screenshots = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.png"))
    if screenshots != report["screenshots"]["paths"]:
        raise ValueError("SCREENSHOT_INVENTORY_MISMATCH")
    for case in report["ui_smoke"]:
        if digest(ROOT / case["scenario"]) != case["scenario_sha256"]:
            raise ValueError("SCENARIO_VERSION_MISMATCH")
    repo = ROOT.parent
    if (repo / ".git").exists():
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        if head != report["baseline_sha"]:
            raise ValueError("BASELINE_HEAD_CHANGED")
        changes = subprocess.check_output(["git", "diff", "HEAD", "--name-only"], cwd=repo, text=True)
        if changes.strip():
            raise ValueError("TRACKED_BASELINE_CHANGED")
        for directory, tree in report["protected_trees"].items():
            actual_tree = subprocess.check_output(["git", "rev-parse", f"HEAD:{directory}"],
                                                  cwd=repo, text=True).strip()
            if actual_tree != tree:
                raise ValueError("PROTECTED_TREE_CHANGED")
        print("Git baseline and protected trees: PASS")
    else:
        print("Git checks: NOT_RUN (standalone archive; use baseline checkout)")
    print(f"Manifest: {len(actual)}/{len(actual)} PASS; generated tests unchanged; evidence consistent")
    print("Course Minimum status remains: " + report["course_minimum_status"])


if __name__ == "__main__":
    main()
