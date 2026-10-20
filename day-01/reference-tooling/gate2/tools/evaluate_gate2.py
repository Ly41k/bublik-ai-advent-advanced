"""Fail-closed documentary validation of the real Mac Gate 2 diagnostic logs."""

import json
import os
from pathlib import Path

from collect_agent_trace import calls, read_events, session_path
from probe_runtime import ROOT, digest, redact

AGENT_KEYS = {
    "status",
    "result_type",
    "agent_config_marker",
    "error_code",
    "missing_fields",
    "result",
    "evidence",
    "performed_actions",
}


def validate_agent(result: dict[str, object], trace: dict[str, object], missing: bool) -> None:
    """A claimed zero count alone is insufficient: require native child evidence."""
    if set(result) != AGENT_KEYS:
        raise ValueError("ArchitectureReport envelope keys do not match the contract")
    if result["result_type"] != "ArchitectureReport":
        raise ValueError("Wrong returned type")
    if result["agent_config_marker"] != "BUBLIK_ARCHITECTURE_REPORT_V1_20261020":
        raise ValueError("Configured agent marker missing")
    if trace.get("status") != "NATIVE_TRACE_EXTRACTED":
        raise ValueError("No extracted native trace")
    if trace.get("configured_agent_type") != "architecture_report":
        raise ValueError("The configured native agent was not selected")
    if not trace.get("parent_result_matches_child") or trace.get("child_result") != result:
        raise ValueError("Parent summary is not the actual child result")
    count = trace.get("child_tool_call_count")
    if (
        type(count) is not int
        or type(result["performed_actions"]) is not int
        or result["performed_actions"] != count
    ):
        raise ValueError("Reported actions do not match observed native tool calls")
    if missing:
        if (
            result["status"] != "BLOCKED"
            or result["error_code"] != "MISSING_REQUIRED_INPUT"
            or result["missing_fields"] != ["task_spec"]
            or result["result"] is not None
            or result["evidence"] != []
            or count != 0
        ):
            raise ValueError("Missing-input contract was not followed before tools")
    else:
        body = result["result"]
        if (
            result["status"] != "SUCCESS"
            or result["error_code"] is not None
            or result["missing_fields"] != []
            or count < 1
            or not isinstance(body, dict)
            or set(body) != {"summary", "files_reviewed", "findings"}
            or not isinstance(body["summary"], str)
            or not body["summary"].strip()
            or not isinstance(body["files_reviewed"], list)
            or not body["files_reviewed"]
            or not isinstance(body["findings"], list)
            or not isinstance(result["evidence"], list)
            or not result["evidence"]
        ):
            raise ValueError("Successful ArchitectureReport contract was not followed")
        for reference in [*body["files_reviewed"], *result["evidence"]]:
            if not isinstance(reference, str):
                raise ValueError("Source reference must be a string")
            path = (ROOT / reference.split("#", 1)[0]).resolve()
            if not path.is_relative_to(ROOT / "src") or not path.is_file():
                raise ValueError("Unverified or out-of-scope source reference")
        for finding in body["findings"]:
            if (
                not isinstance(finding, dict)
                or set(finding) != {"severity", "path", "symbol", "message"}
                or finding["severity"] not in ("HIGH", "MEDIUM", "LOW")
                or not all(isinstance(finding[key], str) and finding[key] for key in finding)
            ):
                raise ValueError("Malformed architecture finding")


def main() -> int:
    folder = ROOT / "local-evidence/gate2"
    output = folder / "mac-gate2-summary.json"
    if output.exists():
        raise SystemExit("Summary exists; preserve it before reviewing a new attempt")
    report: dict[str, object] = {"status": "BLOCKED", "generation_invocations": 0}
    try:
        probe = json.loads((folder / "mac-runtime-probe.json").read_text())
        if probe.get("status") != "PREFLIGHT_PASS" or probe.get("os") != "Darwin":
            raise ValueError("No passing real Mac preflight")
        report["runtime_preflight"] = "PASS"
        for step in ("instructions", "skill", "agent_missing", "agent_success"):
            metadata = json.loads((folder / step / "metadata.json").read_text())
            if metadata.get("exit_code") != 0:
                raise ValueError(f"Diagnostic failed: {step}")
            integrity = json.loads((folder / step / "host-integrity.json").read_text())
            if integrity.get("status") != "PASS":
                raise ValueError(f"Diagnostic changed protected inputs: {step}")
        rules = json.loads((folder / "instructions/result.json").read_text())
        if rules != {
            "global_marker": "BUBLIK_GLOBAL_RULES_V1_20261020",
            "project_marker": "BUBLIK_PROJECT_RULES_V1_20261020",
        }:
            raise ValueError("Startup instruction markers were not actually returned")
        cli_events = read_events(folder / "instructions/events.jsonl")
        ids = [
            str(item["thread_id"]) for item in cli_events if item.get("type") == "thread.started"
        ]
        if len(ids) != 1:
            raise ValueError("Cannot identify native instruction-probe thread")
        home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
        path = session_path(home, ids[0])
        if calls(read_events(path)):
            raise ValueError("Instruction markers were obtained after tools, not at startup")
        report["startup_instructions"] = {
            "status": "PASS",
            "source_sha256": digest(path),
            "native_tool_calls": 0,
        }
        skill = json.loads((folder / "skill/result.json").read_text())
        if (
            skill.get("status") != "PASS"
            or skill.get("skill_marker") != "BUBLIK_QUALITY_GATE_V1_20261020"
            or skill.get("runner_exit_code") != 0
        ):
            raise ValueError("Skill output did not satisfy its success contract")
        events = read_events(folder / "skill/events.jsonl")
        completed = [item["item"] for item in events if item.get("type") == "item.completed"]
        if not any(
            item.get("type") == "command_execution"
            and "scripts/run_checks.py" in str(item.get("command", ""))
            and item.get("exit_code") == 0
            for item in completed
        ):
            raise ValueError("No observed successful execution of the frozen quality-gate runner")
        if not any(".agents/skills/quality-gate/SKILL.md" in str(item) for item in completed):
            raise ValueError("No observed read of the actual project skill instructions")
        skill_log = (folder / "skill-quality-checks.txt").read_text()
        if "overall: PASS" not in skill_log or "38 passed" not in skill_log:
            raise ValueError("Expected baseline quality-gate evidence is absent")
        report["project_skill"] = "PASS"
        for step, missing in (("agent_missing", True), ("agent_success", False)):
            result = json.loads(redact((folder / step / "result.json").read_text()))
            trace = json.loads((folder / step / "native-trace.json").read_text())
            validate_agent(result, trace, missing)
            report[step] = {"status": "PASS", "child_tools": trace["child_tool_call_count"]}
        report["status"] = "EVIDENCE_CHECKS_PASS_REVIEW_REQUIRED"
        report["note"] = (
            "Review raw outputs/screenshots and integrity before declaring Gate 2 PASS."
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        report["error"] = redact(str(error))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(redact(json.dumps(report, indent=2)) + "\n")
    print(report["status"])
    return int(report["status"] == "BLOCKED")


if __name__ == "__main__":
    raise SystemExit(main())
