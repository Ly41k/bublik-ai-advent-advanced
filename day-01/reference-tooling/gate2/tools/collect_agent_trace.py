"""Extract only task-specific native parent/child calls from Codex session logs."""

import argparse
import json
import os
from pathlib import Path
from uuid import UUID

from probe_runtime import ROOT, digest, objects, redact


def read_events(path: Path) -> list[dict[str, object]]:
    """Require real JSONL; malformed records block documentary acceptance."""
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def session_path(home: Path, thread_id: str) -> Path:
    """Read only the explicitly identified task thread, not unrelated sessions."""
    UUID(thread_id)
    matches = list((home / "sessions").rglob(f"*{thread_id}.jsonl"))
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one native log for task thread {thread_id}")
    return matches[0]


def calls(events: list[dict[str, object]]) -> list[dict[str, object]]:
    """Keep actual model tool calls and ignore system/user instruction bodies."""
    result = []
    for number, event in enumerate(events, start=1):
        payload = event.get("payload", {})
        if event.get("type") == "response_item" and isinstance(payload, dict):
            kind = str(payload.get("type", ""))
            if kind.endswith("_call") and not kind.endswith("_call_output"):
                result.append({"source_line": number, "payload": payload})
    return result


def final_json(events: list[dict[str, object]]) -> object:
    messages = []
    for event in events:
        payload = event.get("payload", {})
        if (
            event.get("type") == "response_item"
            and isinstance(payload, dict)
            and payload.get("type") == "message"
            and payload.get("role") == "assistant"
        ):
            for part in payload.get("content", []):
                if isinstance(part, dict) and part.get("type") in ("output_text", "text"):
                    messages.append(str(part.get("text", "")))
    if not messages:
        raise ValueError("No native final assistant response found")
    return json.loads(messages[-1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", choices=("agent_missing", "agent_success"), required=True)
    args = parser.parse_args()
    folder = ROOT / "local-evidence/gate2" / args.step
    target = folder / "native-trace.json"
    if target.exists():
        parser.error("trace already exists; preserve previous evidence")
    cli_events = read_events(folder / "events.jsonl")
    ids = [str(event["thread_id"]) for event in cli_events if event.get("type") == "thread.started"]
    if len(ids) != 1:
        parser.error("Cannot identify a unique native parent thread")
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    parent_path = session_path(home, ids[0])
    parent_events = read_events(parent_path)
    parent_calls = calls(parent_events)
    spawns = []
    for entry in parent_calls:
        payload = entry["payload"]
        if str(payload.get("name", "")).split(".")[-1] == "spawn_agent":
            arguments = json.loads(str(payload.get("arguments", "{}")))
            if arguments.get("agent_type") != "architecture_report":
                raise ValueError("Native spawn did not select the configured architecture_report")
            spawns.append(payload)
    if len(spawns) != 1:
        raise ValueError("Expected one recorded native spawn_agent call, not a textual imitation")
    spawn = spawns[0]
    output = [
        event["payload"]
        for event in parent_events
        if isinstance(event.get("payload"), dict)
        and event["payload"].get("type") == "function_call_output"
        and event["payload"].get("call_id") == spawn.get("call_id")
    ]
    if len(output) != 1:
        raise ValueError("Cannot correlate the spawn with its native tool result")
    spawn_result = json.loads(str(output[0].get("output", "{}")))
    child_ids = {
        str(value)
        for item in objects(spawn_result)
        for key, value in item.items()
        if key in ("agent_id", "thread_id") and isinstance(value, str)
    }
    if len(child_ids) != 1:
        raise ValueError("Native child thread identifier is ambiguous")
    child_id = child_ids.pop()
    child_path = session_path(home, child_id)
    child_events = read_events(child_path)
    child_calls = calls(child_events)
    child_result = final_json(child_events)
    if child_result != json.loads((folder / "result.json").read_text()):
        raise ValueError("Parent result differs from the actual child's JSON")
    report = {
        "status": "NATIVE_TRACE_EXTRACTED",
        "parent_thread_id": ids[0],
        "child_thread_id": child_id,
        "parent_source_sha256": digest(parent_path),
        "child_source_sha256": digest(child_path),
        "configured_agent_type": "architecture_report",
        "spawn_call": spawn,
        "parent_call_count": len(parent_calls),
        "child_tool_calls": child_calls,
        "child_tool_call_count": len(child_calls),
        "child_result": child_result,
        "parent_result_matches_child": True,
    }
    target.write_text(redact(json.dumps(report, indent=2, ensure_ascii=False)) + "\n")
    print(f"Native child tools: {len(child_calls)}; trace saved for review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
