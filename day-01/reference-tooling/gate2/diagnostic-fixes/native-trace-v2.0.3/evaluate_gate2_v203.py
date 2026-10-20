"""Offline aggregate review adapter; preserve all frozen criteria and old reports."""

import argparse
import json
import os
import sys
from pathlib import Path

import collect_agent_trace_v2 as trace

sys.path.insert(0, str(trace.ROOT / "gate2/tools"))
import evaluate_gate2 as frozen  # noqa: E402

STEPS = ("instructions", "skill", "agent_missing", "agent_success")
RULES_RESULT = {"global_marker": "BUBLIK_GLOBAL_RULES_V1_20261020",
                "project_marker": "BUBLIK_PROJECT_RULES_V1_20261020"}


def read(path: Path) -> dict[str, object]:
    return trace.decode(trace.read_bytes(path))


def validate_runs(root: Path) -> dict[str, object]:
    folder = root / "local-evidence/gate2"
    probe = read(folder / "mac-runtime-probe.json")
    trace.require(probe.get("status") == "PREFLIGHT_PASS" and probe.get("os") == "Darwin",
                  "MAC_PREFLIGHT_NOT_PASS")
    hashes = {}
    for step in STEPS:
        path = folder / step
        metadata = read(path / "metadata.json")
        integrity = read(path / "host-integrity.json")
        expected = trace.sha(trace.read_bytes(root / "gate2/diagnostics" / (step + ".txt")))
        sandbox = "workspace-write" if step == "skill" else "read-only"
        trace.require(metadata.get("step") == step and metadata.get("exit_code") == 0
                      and type(metadata.get("exit_code")) is int
                      and metadata.get("codex") == "codex-cli 0.163.0"
                      and metadata.get("python") == "3.13.3" and metadata.get("os") == "Darwin"
                      and metadata.get("sandbox") == sandbox
                      and metadata.get("template_sha256") == expected
                      and type(metadata.get("generation_invocations")) is int
                      and metadata["generation_invocations"] == 0
                      and type(metadata.get("diagnostic_parent_invocations")) is int
                      and metadata["diagnostic_parent_invocations"] == 1,
                      "DIAGNOSTIC_METADATA_NOT_ACCEPTED")
        trace.require(integrity == {"status": "PASS", "changed_files": []},
                      "HOST_INTEGRITY_NOT_PASS")
        hashes[step] = {name: trace.sha(trace.read_bytes(path / name))
                        for name in ("result.json", "metadata.json", "host-integrity.json", "events.jsonl")}
    return hashes


def native_events(folder: Path, index: dict[str, trace.CatalogEntry]) -> tuple[list[dict[str, object]], str]:
    cli = trace.jsonl(trace.read_bytes(folder / "events.jsonl"))
    ids = [trace.identifier(e.get("thread_id")) for e in cli if e.get("type") == "thread.started"]
    trace.require(len(ids) == 1 and ids[0] in index, "DIAGNOSTIC_NATIVE_THREAD_NOT_UNIQUE")
    raw = trace.read_bytes(index[ids[0]].path)
    events = trace.jsonl(raw)
    trace.require(events[0].get("type") == "session_meta"
                  and events[0]["payload"].get("id") == ids[0], "NATIVE_THREAD_ID_CONFLICT")
    return events, trace.sha(raw)


def validate_startup(result: dict[str, object], events: list[dict[str, object]]) -> None:
    trace.require(result == RULES_RESULT, "STARTUP_MARKERS_MISSING")
    calls = trace.response_calls(events)
    trace.require(not calls, "STARTUP_USED_TOOLS")
    trace.child_completion(events, 0)
    trace.require(trace.final_result(events) == result, "STARTUP_NATIVE_RESULT_MISMATCH")


def command_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(part, str) for part in value):
        return " ".join(value)
    return ""


def validate_skill(folder: Path, index: dict[str, trace.CatalogEntry] | None) -> dict[str, object]:
    result = read(folder / "skill/result.json")
    trace.require(result.get("status") == "PASS"
                  and result.get("skill_marker") == "BUBLIK_QUALITY_GATE_V1_20261020"
                  and type(result.get("runner_exit_code")) is int
                  and result["runner_exit_code"] == 0, "SKILL_RESULT_NOT_PASS")
    events = trace.jsonl(trace.read_bytes(folder / "skill/events.jsonl"))
    completed = [e["item"] for e in events if e.get("type") == "item.completed"
                 and isinstance(e.get("item"), dict)]
    runner = any(item.get("type") in {"command_execution", "CommandExecution"}
                 and "scripts/run_checks.py" in command_text(item.get("command"))
                 and type(item.get("exit_code")) is int and item["exit_code"] == 0
                 for item in completed)
    # Same CLI evidence condition as the frozen evaluator, including observed skill read.
    skill_read = any(".agents/skills/quality-gate/SKILL.md" in str(item) for item in completed)
    source_hash = None
    method = "original_cli_events"
    if not (runner and skill_read) and index is not None:
        native, source_hash = native_events(folder / "skill", index)
        thread_id = native[0]["payload"]["id"]
        for event in native:
            payload = event.get("payload", {})
            if not (event.get("type") == "event_msg" and payload.get("type") == "item_completed"
                    and isinstance(payload.get("item"), dict)
                    and payload["item"].get("type") == "CommandExecution"):
                continue
            try:
                trace.native_schema.event(payload, thread_id)
            except trace.native_schema.SchemaError as error:
                raise trace.Blocked(error.code) from error
            item = payload["item"]
            succeeded = item["status"] == "completed" and item["exit_code"] == 0
            command = command_text(item["command"])
            runner = runner or succeeded and "scripts/run_checks.py" in command
            skill_read = skill_read or succeeded and ".agents/skills/quality-gate/SKILL.md" in command
        method = "cli_and_validated_native_command_events"
    trace.require(runner and skill_read, "SKILL_EXECUTION_OR_READ_NOT_PROVEN")
    log = trace.read_bytes(folder / "skill-quality-checks.txt")
    trace.require(b"overall: PASS" in log and b"38 passed" in log, "BASELINE_SKILL_LOG_NOT_PASS")
    return {"status": "PASS", "evidence_method": method, "native_source_sha256": source_hash,
            "checks_log_sha256": trace.sha(log),
            "cli_events_sha256": trace.sha(trace.read_bytes(folder / "skill/events.jsonl"))}


def validate_agent_trace(root: Path, home: Path, step: str,
                         name: str, overlay: dict[str, object]) -> dict[str, object]:
    folder = root / "local-evidence/gate2" / step
    raw = trace.read_bytes(folder / name)
    if step == "agent_missing":
        trace.require(trace.sha(raw) == overlay["accepted_missing_trace_sha256"],
                      "ACCEPTED_MISSING_TRACE_CHANGED")
    saved = trace.decode(raw)
    trace.require(saved.get("status") == "NATIVE_TRACE_EXTRACTED"
                  and saved.get("agent_contract_status") == "PASS"
                  and saved.get("original_evidence_unchanged") is True
                  and saved.get("reported_mac_source_hashes_match") is True
                  and saved.get("codex_invocations_by_collector") == 0
                  and saved.get("generation_invocations") == 0
                  and saved.get("package_verification", {}).get("status") == "PASS",
                  "AGENT_TRACE_NOT_ACCEPTED")
    # Re-extract in memory from existing native logs, without writing or starting a model.
    recomputed = trace.extract(root, home, step)
    source_key = "reported_mac_sources" if step == "agent_missing" else "reported_mac_success_sources"
    trace.verify_reported_sources(recomputed, overlay[source_key])
    for key in ("parent_thread_id", "child_thread_id", "parent_source_sha256", "child_source_sha256",
                "configured_agent_type", "child_tool_call_count", "child_tool_calls", "child_result",
                "parent_result_matches_child"):
        trace.require(saved.get(key) == recomputed.get(key), "STORED_TRACE_NATIVE_MISMATCH")
    originals = saved.get("original_evidence_sha256")
    trace.require(isinstance(originals, dict) and bool(originals), "ORIGINAL_HASHES_MISSING")
    for relative, expected in originals.items():
        path = folder / relative
        trace.require(path.resolve().is_relative_to(folder.resolve()), "UNSAFE_EVIDENCE_HASH_PATH")
        trace.require(trace.sha(trace.read_bytes(path)) == expected, "ORIGINAL_EVIDENCE_CHANGED")
    result = trace.decode(frozen.redact(trace.read_bytes(folder / "result.json").decode()))
    frozen.validate_agent(result, saved, missing=step == "agent_missing")
    return {"status": "PASS", "child_tools": saved["child_tool_call_count"],
            "trace_file": name, "trace_sha256": trace.sha(raw),
            "parent_source_sha256": saved["parent_source_sha256"],
            "child_source_sha256": saved["child_source_sha256"],
            "command_execution_audit": recomputed.get("command_execution_audit")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-name", default="mac-gate2-summary.v2.0.3.json")
    args = parser.parse_args(argv)
    root = trace.ROOT
    folder = root / "local-evidence/gate2"
    valid_name = (Path(args.output_name).name == args.output_name
                  and args.output_name.startswith("mac-gate2-summary.v2.0.3")
                  and args.output_name.endswith(".json"))
    if not valid_name:
        print(json.dumps({"status": "BLOCKED", "error_code": "INVALID_OUTPUT_NAME"}))
        return 1
    output = folder / args.output_name
    report: dict[str, object] = {"status": "BLOCKED", "generation_invocations": 0,
                                "codex_invocations_by_evaluator": 0,
                                "evaluator_version": trace.VERSION,
                                "generation_allowed": False}
    try:
        trace.require(folder.is_dir(), "EVIDENCE_DIRECTORY_MISSING")
        trace.require(not output.exists() and not output.is_symlink(), "OUTPUT_ALREADY_EXISTS")
        report["package_verification"] = trace.verify(root)
        overlay = read(trace.FIX_DIR / "manifest.json")
        report["diagnostic_evidence_sha256"] = validate_runs(root)
        report["runtime_preflight"] = "PASS"
        report["runtime_preflight_sha256"] = trace.sha(trace.read_bytes(folder / "mac-runtime-probe.json"))
        home = Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser()
        index = trace.catalog(home)
        events, source_hash = native_events(folder / "instructions", index)
        validate_startup(read(folder / "instructions/result.json"), events)
        report["startup_instructions"] = {"status": "PASS", "source_sha256": source_hash,
                                          "native_tool_calls": 0}
        report["project_skill"] = validate_skill(folder, index)
        for step, name in (("agent_missing", "native-trace.v2.0.2.json"),
                           ("agent_success", "native-trace.v2.0.3.json")):
            report[step] = validate_agent_trace(root, home, step, name, overlay)
        report["status"] = "EVIDENCE_CHECKS_PASS_REVIEW_REQUIRED"
        report["note"] = "Review the retained raw evidence and this summary before Gate 2 acceptance."
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        report["error_code"] = error.code if isinstance(error, trace.Blocked) else "EVIDENCE_INVALID_OR_UNAVAILABLE"
        if output.exists() or output.is_symlink() or not folder.is_dir():
            print(json.dumps({"status": "BLOCKED", "error_code": report["error_code"]}))
            return 1
    trace.write_new(output, report, root)
    print(json.dumps({key: report[key] for key in ("status", "error_code", "generation_allowed") if key in report}))
    return int(report["status"] == "BLOCKED")


if __name__ == "__main__":
    raise SystemExit(main())
