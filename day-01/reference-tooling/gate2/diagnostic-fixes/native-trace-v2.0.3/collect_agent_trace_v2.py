"""Offline native trace extraction; no Codex invocation, network or log mutation."""

import argparse
import hashlib
import json
import os
import platform
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import native_schema_0163 as native_schema

VERSION = "native-trace-v2.0.3"
FIX_DIR = Path(__file__).resolve().parent
ROOT = FIX_DIR.parents[2]
MAX_META_BYTES = 4 * 1024 * 1024
NON_CALL_ITEMS = {
    "message", "reasoning", "function_call_output", "custom_tool_call_output", "agent_message"
}
BENIGN_EVENTS = {
    "token_count", "agent_message", "agent_message_delta", "agent_reasoning",
    "agent_reasoning_delta", "agent_reasoning_raw_content", "agent_reasoning_raw_content_delta",
    "agent_reasoning_section_break", "user_message", "warning", "model_reroute",
}
TOOL_EVENTS = {
    "exec_command_begin", "exec_command_end", "exec_command_output_delta",
    "mcp_tool_call_begin", "mcp_tool_call_end", "web_search_begin", "web_search_end",
    "image_generation_begin", "image_generation_end", "patch_apply_begin", "patch_apply_end",
    "collab_agent_spawn_begin", "collab_agent_spawn_end", "collab_agent_interaction_begin",
    "collab_agent_interaction_end", "dynamic_tool_call_request", "view_image_tool_call",
}


class Blocked(ValueError):
    """Expose only a stable diagnostic code, never raw log contents."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Blocked(code)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def decode(raw: bytes | str) -> dict[str, object]:
    try:
        value = json.loads(raw, object_pairs_hook=no_duplicate_keys)
    except (ValueError, UnicodeError) as error:
        raise Blocked("INVALID_JSON") from error
    require(isinstance(value, dict), "EXPECTED_JSON_OBJECT")
    return value


def identifier(value: object) -> str:
    require(isinstance(value, str), "INVALID_NATIVE_ID")
    try:
        result = str(UUID(value))
    except ValueError as error:
        raise Blocked("INVALID_NATIVE_ID") from error
    require(value == result, "NONCANONICAL_NATIVE_ID")
    return result


def read_bytes(path: Path) -> bytes:
    require(not path.is_symlink(), "SYMLINK_INPUT")
    return path.read_bytes()


def metadata(raw: bytes) -> dict[str, object]:
    record = decode(raw)
    require(record.get("type") == "session_meta", "MISSING_FIRST_SESSION_META")
    payload = record.get("payload")
    require(isinstance(payload, dict), "INVALID_SESSION_META")
    identifier(payload.get("id"))
    return payload


@dataclass(frozen=True)
class CatalogEntry:
    path: Path
    first_record: bytes
    meta: dict[str, object]


def inventory_error(error: OSError) -> None:
    """An unreadable subtree makes a uniqueness claim unproven."""
    raise Blocked("SESSION_INVENTORY_UNREADABLE") from error


def catalog(home: Path) -> dict[str, CatalogEntry]:
    """Canonicalize host ancestors; reject links at and inside the native log root."""
    require(not home.is_symlink(), "SYMLINK_INPUT")
    # macOS temporary directories commonly have an ancestor /var -> /private/var.
    # Resolve the supplied home once, then enforce the boundary below that root.
    directory = home.resolve(strict=True) / "sessions"
    require(directory.is_dir() and not directory.is_symlink(), "SESSIONS_UNAVAILABLE")
    result: dict[str, CatalogEntry] = {}
    for current, directories, filenames in os.walk(
        directory, followlinks=False, onerror=inventory_error
    ):
        base = Path(current)
        # Unlike rglob, explicitly reject a link that would otherwise be skipped.
        for name in directories:
            require(not (base / name).is_symlink(), "SYMLINK_INPUT")
        for name in filenames:
            if not name.endswith(".jsonl"):
                continue
            path = base / name
            require(not path.is_symlink(), "SYMLINK_INPUT")
            with path.open("rb") as stream:
                first = stream.readline(MAX_META_BYTES + 1)
            require(len(first) <= MAX_META_BYTES, "OVERSIZED_SESSION_META")
            require(first.endswith(b"\n"), "INCOMPLETE_SESSION_META")
            meta = metadata(first)
            key = identifier(meta["id"])
            require(key not in result, "DUPLICATE_SESSION_ID")
            result[key] = CatalogEntry(path, first, meta)
    require(bool(result), "NO_SESSION_METADATA")
    return result


def select_child(index: dict[str, CatalogEntry], parent_id: str) -> str:
    """Use explicit native spawn ancestry, never names, filenames or timestamps."""
    require(parent_id in index, "PARENT_SESSION_NOT_FOUND")
    candidates: list[str] = []
    for child_id, entry in index.items():
        source = entry.meta.get("source")
        subagent = source.get("subagent") if isinstance(source, dict) else None
        spawn = subagent.get("thread_spawn") if isinstance(subagent, dict) else None
        nested = spawn.get("parent_thread_id") if isinstance(spawn, dict) else None
        top = entry.meta.get("parent_thread_id")
        if isinstance(subagent, dict) and "thread_spawn" in subagent:
            require(isinstance(spawn, dict), "INVALID_SPAWN_METADATA")
            identifier(nested)
            if "parent_thread_id" in entry.meta:
                identifier(top)
                require(top == nested, "CONFLICTING_PARENT_METADATA")
        if nested != parent_id and top != parent_id:
            continue
        require(child_id != parent_id, "SELF_PARENT_LINK")
        require(isinstance(spawn, dict) and nested == parent_id, "UNPROVEN_SPAWN_ANCESTRY")
        require(top is None or top == nested, "CONFLICTING_PARENT_METADATA")
        depth = spawn.get("depth")
        require(type(depth) is int and depth >= 1, "INVALID_SPAWN_DEPTH")
        candidates.append(child_id)
    require(bool(candidates), "CHILD_LINK_NOT_FOUND")
    require(len(candidates) == 1, "CHILD_LINK_AMBIGUOUS")
    return candidates[0]


def jsonl(raw: bytes) -> list[dict[str, object]]:
    require(bool(raw) and raw.endswith(b"\n"), "TRUNCATED_JSONL")
    lines = raw.splitlines()
    require(all(line.strip() for line in lines), "BLANK_JSONL_RECORD")
    return [decode(line) for line in lines]


def response_calls(events: list[dict[str, object]]) -> list[dict[str, object]]:
    require(bool(events) and events[0].get("type") == "session_meta", "MISSING_FIRST_SESSION_META")
    thread_id = identifier(events[0]["payload"].get("id"))
    result = []
    for line, event in enumerate(events, 1):
        kind = event.get("type")
        require(kind in {"session_meta", "turn_context", "response_item", "event_msg"}
                | native_schema.AUXILIARY_RECORDS,
                "UNSUPPORTED_NATIVE_RECORD")
        payload = event.get("payload")
        require(isinstance(payload, dict), "INVALID_NATIVE_PAYLOAD")
        try:
            if kind in native_schema.AUXILIARY_RECORDS:
                native_schema.auxiliary(kind, payload, thread_id)
            elif kind == "event_msg" and payload.get("type") in {
                "thread_settings_applied", "item_completed"
            }:
                native_schema.event(payload, thread_id)
            elif kind == "response_item" and payload.get("type") == "agent_message":
                native_schema.agent_message(payload)
        except native_schema.SchemaError as error:
            raise Blocked(error.code) from error
        if kind != "response_item":
            continue
        item_type = payload.get("type")
        require(isinstance(item_type, str), "INVALID_RESPONSE_ITEM")
        if item_type.endswith("_call"):
            result.append({"source_line": line, "payload": payload})
        else:
            require(item_type in NON_CALL_ITEMS, "UNSUPPORTED_RESPONSE_ITEM")
    return result


def spawn_info(events: list[dict[str, object]]) -> tuple[dict[str, object], dict[str, object]]:
    spawns = []
    for entry in response_calls(events):
        payload = entry["payload"]
        if str(payload.get("name", "")).split(".")[-1] == "spawn_agent":
            spawns.append(payload)
    require(len(spawns) == 1, "EXPECTED_ONE_NATIVE_SPAWN")
    spawn = spawns[0]
    require(spawn.get("type") == "function_call", "UNSUPPORTED_SPAWN_CALL")
    arguments = spawn.get("arguments")
    require(isinstance(arguments, str), "INVALID_SPAWN_ARGUMENTS")
    require(decode(arguments).get("agent_type") == "architecture_report", "WRONG_AGENT_TYPE")
    call_id = spawn.get("call_id")
    require(isinstance(call_id, str) and bool(call_id), "MISSING_SPAWN_CALL_ID")
    outputs = [
        event["payload"] for event in events
        if event.get("type") == "response_item"
        and event["payload"].get("type") == "function_call_output"
        and event["payload"].get("call_id") == call_id
    ]
    require(len(outputs) == 1, "SPAWN_OUTPUT_NOT_UNIQUE")
    output = outputs[0].get("output")
    require(isinstance(output, str), "INVALID_SPAWN_OUTPUT")
    return spawn, decode(output)


def check_spawn_response(response: dict[str, object], child_id: str) -> str:
    if set(response) == {"task_name"}:
        require(isinstance(response["task_name"], str) and bool(response["task_name"].strip()),
                "INVALID_TASK_NAME_RESPONSE")
        return "task_name_only_not_used_for_identity"
    ids: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            require("error" not in value, "SPAWN_RETURNED_ERROR")
            for key, item in value.items():
                if key in {"agent_id", "thread_id"}:
                    ids.add(identifier(item))
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(response)
    require(bool(ids), "UNSUPPORTED_SPAWN_RESPONSE")
    require(ids == {child_id}, "SPAWN_ID_METADATA_CONFLICT")
    return "native_id_cross_checked_with_metadata"


def final_result(events: list[dict[str, object]]) -> dict[str, object]:
    messages = []
    for event in events:
        payload = event.get("payload", {})
        if (event.get("type") == "response_item" and payload.get("type") == "message"
                and payload.get("role") == "assistant"):
            content = payload.get("content")
            require(isinstance(content, list) and bool(content), "INVALID_ASSISTANT_CONTENT")
            require(all(isinstance(p, dict) and p.get("type") in {"text", "output_text", "input_text"}
                        and isinstance(p.get("text"), str) for p in content),
                    "UNSUPPORTED_ASSISTANT_CONTENT")
            messages.append("".join(part["text"] for part in content))
    require(bool(messages), "NO_FINAL_ASSISTANT_MESSAGE")
    return decode(messages[-1])


def child_completion(events: list[dict[str, object]], count: int) -> dict[str, object]:
    starts = []
    ends = []
    tool_events = []
    completed_items = []
    for line, event in enumerate(events, 1):
        if event.get("type") != "event_msg":
            continue
        payload = event["payload"]
        kind = payload.get("type")
        if kind == "task_started":
            starts.append((line, payload))
        elif kind == "task_complete":
            ends.append((line, payload))
        elif kind in TOOL_EVENTS:
            tool_events.append(kind)
        elif kind == "thread_settings_applied":
            pass  # Already schema-validated by response_calls, not an action.
        elif kind == "item_completed":
            completed_items.append((line, payload))
            if payload["item"]["type"] in native_schema.ACTION_ITEMS:
                tool_events.append("item_completed." + payload["item"]["type"])
        else:
            require(kind in BENIGN_EVENTS, "UNSUPPORTED_OR_FAILED_CHILD_EVENT")
    require(len(starts) == 1 and len(ends) == 1, "CHILD_COMPLETION_NOT_PROVEN")
    start_line, start = starts[0]
    end_line, end = ends[0]
    require(start_line < end_line, "INVALID_CHILD_TURN_ORDER")
    require(isinstance(start.get("turn_id"), str) and bool(start["turn_id"])
            and start["turn_id"] == end.get("turn_id"), "CHILD_TURN_ID_CONFLICT")
    for line, payload in completed_items:
        require(start_line < line < end_line, "COMPLETED_ITEM_OUTSIDE_CHILD_TURN")
        require(payload["turn_id"] == start["turn_id"], "COMPLETED_ITEM_TURN_CONFLICT")
    for line, event in enumerate(events, 1):
        if (event.get("type") == "response_item"
                and not (event["payload"].get("type") == "message"
                         and event["payload"].get("role") in {"user", "developer", "system"})):
            require(start_line < line < end_line, "REPLAYED_OR_OUTSIDE_TURN_HISTORY")
    require(count > 0 or not tool_events, "TOOL_EVENTS_WITHOUT_CALL_RECORD")
    calls = response_calls(events)
    call_ids = {entry["payload"].get("call_id") for entry in calls}
    for event in events:
        payload = event["payload"]
        if (event.get("type") == "response_item"
                and payload.get("type") in {"function_call_output", "custom_tool_call_output"}):
            require(isinstance(payload.get("call_id"), str)
                    and payload["call_id"] in call_ids, "TOOL_OUTPUT_WITHOUT_CALL_RECORD")
    if end.get("last_agent_message") is not None:
        require(isinstance(end["last_agent_message"], str)
                and decode(end["last_agent_message"]) == final_result(events),
                "COMPLETION_RESULT_CONFLICT")
    return {"event_type": "task_complete", "turn_id": start["turn_id"],
            "source_line": end_line, "tool_event_count": len(tool_events)}


def files_snapshot(folder: Path) -> dict[str, str]:
    return {path.relative_to(folder).as_posix(): sha(read_bytes(path))
            for path in folder.rglob("*") if path.is_file()}


def safe_call(entry: dict[str, object]) -> dict[str, object]:
    payload = entry["payload"]
    return {"source_line": entry["source_line"], "type": payload["type"],
            "payload_sha256": sha(json.dumps(payload, sort_keys=True).encode())}


def command_execution_audit(events: list[dict[str, object]],
                            entries: list[dict[str, object]]) -> dict[str, object]:
    """Audit command events separately; their IDs are not assumed to be model-call IDs."""
    commands = [event["payload"]["item"] for event in events
                if event.get("type") == "event_msg"
                and event["payload"].get("type") == "item_completed"
                and event["payload"]["item"]["type"] == "CommandExecution"]
    require(bool(commands) and bool(entries), "SUCCESSFUL_COMMAND_EVIDENCE_MISSING")
    for command in commands:
        require(command["status"] == "completed" and command["exit_code"] == 0,
                "COMMAND_EXECUTION_NOT_SUCCESSFUL")
    call_ids = []
    for entry in entries:
        call = entry["payload"]
        require(call["type"] in {"function_call", "custom_tool_call"},
                "SUCCESS_NATIVE_CALL_TYPE_NOT_SUPPORTED")
        call_id = call.get("call_id")
        require(isinstance(call_id, str) and bool(call_id), "INVALID_NATIVE_CALL_ID")
        call_ids.append(call_id)
        outputs = [event["payload"] for event in events
                   if event.get("type") == "response_item"
                   and event["payload"].get("type") == call["type"] + "_output"
                   and event["payload"].get("call_id") == call_id]
        require(len(outputs) == 1, "NATIVE_CALL_COMPLETION_NOT_UNIQUE")
    require(bool(call_ids), "SUCCESS_NATIVE_CALL_TYPE_NOT_SUPPORTED")
    require(len(set(call_ids)) == len(call_ids), "DUPLICATE_NATIVE_CALL_ID")
    return {"response_item_call_count": len(entries), "completed_command_item_count": len(commands),
            "all_commands_completed_exit_zero": True,
            "native_call_outputs_correlated_by_call_id": True,
            "command_item_ids_assumed_to_be_call_ids": False,
            "command_item_count_added_to_call_count": False}


def extract(root: Path, home: Path, step: str) -> dict[str, object]:
    folder = root / "local-evidence/gate2" / step
    before = files_snapshot(folder)
    require(bool(before), "EVIDENCE_DIRECTORY_MISSING")
    cli = jsonl(read_bytes(folder / "events.jsonl"))
    parent_ids = [identifier(event.get("thread_id")) for event in cli
                  if event.get("type") == "thread.started"]
    require(len(parent_ids) == 1, "PARENT_CLI_ID_NOT_UNIQUE")
    require(sum(event.get("type") == "turn.completed" for event in cli) == 1
            and not any(event.get("type") in {"error", "turn.failed"} for event in cli),
            "PARENT_CLI_COMPLETION_NOT_PROVEN")
    run = decode(read_bytes(folder / "metadata.json"))
    require(run.get("codex") == "codex-cli 0.163.0" and run.get("step") == step
            and type(run.get("exit_code")) is int and run["exit_code"] == 0,
            "ORIGINAL_DIAGNOSTIC_NOT_SUCCESSFUL")
    integrity = decode(read_bytes(folder / "host-integrity.json"))
    require(integrity.get("status") == "PASS" and integrity.get("changed_files") == [],
            "ORIGINAL_HOST_INTEGRITY_NOT_PASS")
    index = catalog(home)
    parent_id = parent_ids[0]
    child_id = select_child(index, parent_id)
    parent_raw = read_bytes(index[parent_id].path)
    child_raw = read_bytes(index[child_id].path)
    require(parent_raw.splitlines(keepends=True)[0] == index[parent_id].first_record
            and child_raw.splitlines(keepends=True)[0] == index[child_id].first_record,
            "SESSION_CHANGED_DURING_EXTRACTION")
    parent_events, child_events = jsonl(parent_raw), jsonl(child_raw)
    require(sum(e.get("type") == "session_meta" for e in parent_events) == 1
            and sum(e.get("type") == "session_meta" for e in child_events) == 1,
            "REPEATED_SESSION_META")
    spawn, response = spawn_info(parent_events)
    response_mode = check_spawn_response(response, child_id)
    child_calls = response_calls(child_events)
    completion = child_completion(child_events, len(child_calls))
    result = final_result(child_events)
    require(result == decode(read_bytes(folder / "result.json")), "PARENT_RESULT_MISMATCH")
    require(final_result(parent_events) == result, "PARENT_NATIVE_RESULT_MISMATCH")
    require(parent_raw == read_bytes(index[parent_id].path)
            and child_raw == read_bytes(index[child_id].path), "SESSION_CHANGED_DURING_EXTRACTION")
    again = catalog(home)
    require(set(index) == set(again) and all(index[k] == again[k] for k in index),
            "METADATA_INVENTORY_CHANGED")
    require(before == files_snapshot(folder), "ORIGINAL_EVIDENCE_CHANGED")
    command_audit = command_execution_audit(child_events, child_calls) if step == "agent_success" else None
    report: dict[str, object] = {
        "status": "NATIVE_TRACE_EXTRACTED", "extraction_tool_version": VERSION,
        "parent_thread_id": parent_id, "child_thread_id": child_id,
        "parent_source_sha256": sha(parent_raw), "child_source_sha256": sha(child_raw),
        "configured_agent_type": "architecture_report",
        "spawn_call": {"type": spawn["type"], "name": spawn["name"],
                       "call_id": spawn["call_id"],
                       "arguments_sha256": sha(spawn["arguments"].encode())},
        "correlation": {"method": "session_meta.source.subagent.thread_spawn.parent_thread_id",
                        "parent_thread_id": parent_id, "linked_child_count": 1,
                        "parent_session_meta_sha256": sha(index[parent_id].first_record),
                        "child_session_meta_sha256": sha(index[child_id].first_record),
                        "source_line": 1,
                        "top_level_parent_thread_id_present":
                            "parent_thread_id" in index[child_id].meta,
                        "spawn_response_mode": response_mode, "metadata_files_scanned": len(index)},
        "parent_call_count": len(response_calls(parent_events)),
        "child_tool_calls": [safe_call(entry) for entry in child_calls],
        "child_tool_call_count": len(child_calls), "child_result": result,
        "parent_result_matches_child": True, "child_completion": completion,
        "child_response_item_types": dict(Counter(e["payload"]["type"] for e in child_events
                                                 if e.get("type") == "response_item")),
        "native_schema_profile": "codex-cli-0.163.0-mac-observed-v2",
        "tool_call_count_definition": "native response_item types ending in _call (unchanged)",
        "command_execution_audit": command_audit,
        "child_completed_item_types": dict(Counter(
            e["payload"]["item"]["type"] for e in child_events
            if e.get("type") == "event_msg" and e["payload"].get("type") == "item_completed"
        )),
        "child_auxiliary_record_types": dict(Counter(
            e["type"] for e in child_events if e["type"] in native_schema.AUXILIARY_RECORDS
        )),
        "opaque_agent_content_inspected": False,
        "original_evidence_sha256": before, "original_evidence_unchanged": True,
        "codex_invocations_by_collector": 0, "generation_invocations": 0,
    }
    return report


def verify(root: Path) -> dict[str, object]:
    """Keep the original frozen manifest intact; verify a separate overlay manifest."""
    overlay = decode(read_bytes(FIX_DIR / "manifest.json"))
    expected_base = overlay.get("original_frozen_manifest_sha256")
    frozen = read_bytes(root / "gate2/frozen-manifest.json")
    require(sha(frozen) == expected_base, "ORIGINAL_MANIFEST_HASH_MISMATCH")
    groups = [
        (root, decode(frozen).get("files")),
        (root, overlay.get("previous_overlay_files")),
        (FIX_DIR, overlay.get("files")),
    ]
    for directory, entries in groups:
        require(isinstance(entries, dict) and bool(entries), "INVALID_HASH_MANIFEST")
        for name, expected in entries.items():
            require(isinstance(name, str) and isinstance(expected, str), "INVALID_HASH_ENTRY")
            path = directory / name
            require(path.resolve().is_relative_to(directory.resolve()), "UNSAFE_MANIFEST_PATH")
            require(sha(read_bytes(path)) == expected, "PROTECTED_OR_OVERLAY_FILE_CHANGED")
    baseline = read_bytes(root / "weeks/week-01/evidence/day-01/baseline-core.sha256").decode()
    for line in baseline.splitlines():
        expected, name = line.split("  ", 1)
        require(sha(read_bytes(root / name)) == expected, "BASELINE_CHANGED")
    return {"status": "PASS", "tool_version": VERSION, "original_manifest_unchanged": True,
            "previous_overlay_unchanged": True,
            "original_collector_sha256": overlay["original_collector_sha256"],
            "overlay_manifest_sha256": sha(read_bytes(FIX_DIR / "manifest.json")),
            "codex_invocations": 0}


def write_new(path: Path, report: dict[str, object], root: Path) -> None:
    text = json.dumps(report, indent=2, ensure_ascii=False)
    text = text.replace(str(root), "<REPO>").replace(str(Path.home()), "<HOME>")
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text + "\n")


def verify_reported_sources(report: dict[str, object], expected: dict[str, str]) -> None:
    """Recover exactly the already reported first Mac native logs, not a later run."""
    require(set(expected) == {"parent", "child"}, "INVALID_REPORTED_SOURCE_HASHES")
    for role, digest in expected.items():
        require(report.get(role + "_source_sha256") == digest, "REPORTED_NATIVE_SOURCE_CHANGED")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Verify hashes only; no model calls")
    parser.add_argument("--step", choices=("agent_missing", "agent_success"))
    parser.add_argument("--output-name", default="native-trace.v2.0.3.json")
    args = parser.parse_args(argv)
    try:
        verified = verify(ROOT)
        if args.verify:
            require(args.step is None, "VERIFY_AND_STEP_ARE_EXCLUSIVE")
            print(json.dumps(verified))
            return 0
        require(args.step is not None, "STEP_REQUIRED")
        folder = ROOT / "local-evidence/gate2" / args.step
        require(Path(args.output_name).name == args.output_name
                and args.output_name.startswith("native-trace.v2")
                and args.output_name.endswith(".json"), "INVALID_OUTPUT_NAME")
        target = folder / args.output_name
        require(folder.is_dir(), "EVIDENCE_DIRECTORY_MISSING")
        require(not target.exists() and not target.is_symlink(), "OUTPUT_ALREADY_EXISTS")
        try:
            report = extract(ROOT, Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser(),
                             args.step)
            overlay = decode(read_bytes(FIX_DIR / "manifest.json"))
            source_key = ("reported_mac_sources" if args.step == "agent_missing"
                          else "reported_mac_success_sources")
            verify_reported_sources(report, overlay[source_key])
            report["reported_mac_source_hashes_match"] = True
            # Reuse the ORIGINAL contract validator; no acceptance criteria are changed.
            sys.path.insert(0, str(ROOT / "gate2/tools"))
            from evaluate_gate2 import validate_agent

            try:
                validate_agent(report["child_result"], report, missing=args.step == "agent_missing")
                report["agent_contract_status"] = "PASS"
            except ValueError:
                report["agent_contract_status"] = "FAIL"
                report["error_code"] = "ORIGINAL_AGENT_CONTRACT_REJECTED"
        except (Blocked, OSError, ValueError, KeyError, TypeError) as error:
            report = {"status": "BLOCKED", "extraction_tool_version": VERSION,
                      "error_code": (error.code if isinstance(error, Blocked)
                                     else "INPUT_UNAVAILABLE_OR_INVALID"),
                      "codex_invocations_by_collector": 0, "generation_invocations": 0}
        report["package_verification"] = verified
        report["collector_environment"] = {
            "os": platform.system(), "python": platform.python_version()
        }
        write_new(target, report, ROOT)
        keys = ("status", "agent_contract_status", "child_tool_call_count",
                "reported_mac_source_hashes_match", "error_code")
        print(json.dumps({key: report[key] for key in keys if key in report}))
        return int(report.get("agent_contract_status") != "PASS")
    except (Blocked, OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({
            "status": "BLOCKED",
            "error_code": (error.code if isinstance(error, Blocked)
                           else "INPUT_UNAVAILABLE_OR_INVALID"), "codex_invocations": 0
        }))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
