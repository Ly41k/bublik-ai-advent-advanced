"""Exactly two developer instruction bundles; no additional agent roles."""

from core import ROOT, require

PROFILES = {"researcher": "Researcher:", "tester": "Bug Fix Engineer:"}


def instructions(profile: str) -> str:
    require(profile in PROFILES, "UNKNOWN_PROFILE")
    name = "researcher" if profile == "researcher" else "bug_fix_engineer"
    return (
        (ROOT / "profiles/common.md").read_text()
        + "\n"
        + (ROOT / f"profiles/{name}.md").read_text()
    )


def parse(line: str, active: str | None) -> tuple[str, str]:
    value = line.strip()
    require(bool(value), "EMPTY_INPUT")
    if value.startswith("/"):
        parts = value.split(maxsplit=1)
        command = parts[0]
        value = parts[1] if len(parts) == 2 else ""
        require(command[1:] in PROFILES, "UNKNOWN_COMMAND")
        return command[1:], value.strip()
    require(active in PROFILES, "PROFILE_REQUIRED")
    return active, value
