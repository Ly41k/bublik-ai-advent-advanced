"""Synthetic offline tests; never constitute Mac native runtime evidence."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collect_agent_trace_v2 as trace

sys.path.insert(0, str(trace.ROOT / "gate2/tools"))
from evaluate_gate2 import validate_agent  # noqa: E402

PARENT = "01a15636-40ad-7bd0-b39c-3c221e4f1552"
CHILD = "01a15636-50a3-7e22-933a-bbc7a6ddae71"
OTHER = "00000000-0000-4000-8000-000000000003"
RESULT = {
    "status": "BLOCKED", "result_type": "ArchitectureReport",
    "agent_config_marker": "BUBLIK_ARCHITECTURE_REPORT_V1_20261020",
    "error_code": "MISSING_REQUIRED_INPUT", "missing_fields": ["task_spec"],
    "result": None, "evidence": [], "performed_actions": 0,
}


def record(kind: str, payload: dict[str, object]) -> dict[str, object]:
    return {"type": kind, "payload": payload}


def message(result: dict[str, object]) -> dict[str, object]:
    return record("response_item", {"type": "message", "role": "assistant",
                                   "content": [{"type": "output_text", "text": json.dumps(result)}]})


def encoded(events: list[dict[str, object]]) -> bytes:
    return ("\n".join(json.dumps(event) for event in events) + "\n").encode()


class NativeTraceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.home = Path(self.temp.name) / "codex-home"
        self.folder = self.root / "local-evidence/gate2/agent_missing"
        self.folder.mkdir(parents=True)
        (self.home / "sessions").mkdir(parents=True)
        (self.folder / "events.jsonl").write_bytes(encoded([
            {"type": "thread.started", "thread_id": PARENT}, {"type": "turn.completed"}]))
        (self.folder / "result.json").write_text(json.dumps(RESULT))
        (self.folder / "metadata.json").write_text(json.dumps({
            "codex": "codex-cli 0.163.0", "step": "agent_missing", "exit_code": 0}))
        (self.folder / "host-integrity.json").write_text(json.dumps({
            "status": "PASS", "changed_files": []}))
        self.parent = [
            record("session_meta", {"id": PARENT, "source": "cli"}),
            record("response_item", {"type": "function_call", "name": "collaboration.spawn_agent",
                                     "call_id": "spawn-1", "arguments": json.dumps({
                                         "agent_type": "architecture_report", "message": "synthetic"})}),
            record("response_item", {"type": "function_call_output", "call_id": "spawn-1",
                                     "output": json.dumps({"task_name": "/synthetic/architecture_report"})}),
            message(RESULT),
        ]
        self.child = [
            record("session_meta", {"id": CHILD, "parent_thread_id": PARENT,
                                    "source": {"subagent": {"thread_spawn": {
                                        "parent_thread_id": PARENT, "depth": 1,
                                        "agent_role": "architecture_report", "agent_nickname": "synthetic",
                                        "future_metadata": "unused"}}}}),
            record("event_msg", {"type": "task_started", "turn_id": "child-turn-1"}),
            message(RESULT),
            record("event_msg", {"type": "task_complete", "turn_id": "child-turn-1",
                                 "last_agent_message": json.dumps(RESULT)}),
        ]
        self.save()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def save(self) -> None:
        (self.home / "sessions/parent.jsonl").write_bytes(encoded(self.parent))
        (self.home / "sessions/child.jsonl").write_bytes(encoded(self.child))

    def extract(self) -> dict[str, object]:
        self.save()
        return trace.extract(self.root, self.home, "agent_missing")

    def blocked(self, code: str) -> None:
        with self.assertRaises(trace.Blocked) as caught:
            self.extract()
        self.assertEqual(caught.exception.code, code)

    def test_task_name_only_uses_explicit_native_metadata(self) -> None:
        result = self.extract()
        self.assertEqual(result["child_thread_id"], CHILD)
        self.assertEqual(result["child_tool_call_count"], 0)
        self.assertEqual(result["correlation"]["spawn_response_mode"],
                         "task_name_only_not_used_for_identity")
        validate_agent(result["child_result"], result, missing=True)

    def test_task_name_is_not_an_identity_selector(self) -> None:
        self.parent[2]["payload"]["output"] = json.dumps({"task_name": OTHER})
        self.assertEqual(self.extract()["child_thread_id"], CHILD)

    def test_no_parent_link_blocks_despite_matching_task_name(self) -> None:
        self.child[0]["payload"]["parent_thread_id"] = OTHER
        self.child[0]["payload"]["source"]["subagent"]["thread_spawn"]["parent_thread_id"] = OTHER
        self.blocked("CHILD_LINK_NOT_FOUND")

    def test_two_children_with_same_parent_are_ambiguous(self) -> None:
        other = copy.deepcopy(self.child)
        other[0]["payload"]["id"] = OTHER
        (self.home / "sessions/other.jsonl").write_bytes(encoded(other))
        self.blocked("CHILD_LINK_AMBIGUOUS")

    def test_explicit_response_id_does_not_resolve_two_parent_links(self) -> None:
        self.parent[2]["payload"]["output"] = json.dumps({"agent_id": CHILD})
        self.test_two_children_with_same_parent_are_ambiguous()

    def test_conflicting_top_and_nested_parent_blocks(self) -> None:
        self.child[0]["payload"]["parent_thread_id"] = OTHER
        self.blocked("CONFLICTING_PARENT_METADATA")

    def test_top_level_parent_alone_is_not_spawn_proof(self) -> None:
        self.child[0]["payload"]["source"] = "cli"
        self.blocked("UNPROVEN_SPAWN_ANCESTRY")

    def test_nested_explicit_spawn_link_without_optional_top_level(self) -> None:
        del self.child[0]["payload"]["parent_thread_id"]
        self.assertEqual(self.extract()["child_thread_id"], CHILD)

    def test_conflicting_response_uuid_blocks(self) -> None:
        self.parent[2]["payload"]["output"] = json.dumps({"agent_id": OTHER})
        self.blocked("SPAWN_ID_METADATA_CONFLICT")

    def test_legacy_response_uuid_must_agree_with_native_link(self) -> None:
        self.parent[2]["payload"]["output"] = json.dumps({"agent_id": CHILD})
        self.assertEqual(self.extract()["child_thread_id"], CHILD)

    def test_multiple_response_ids_block(self) -> None:
        self.parent[2]["payload"]["output"] = json.dumps({"agent_id": CHILD, "thread_id": OTHER})
        self.blocked("SPAWN_ID_METADATA_CONFLICT")

    def test_filename_does_not_supply_identity(self) -> None:
        self.save()
        source = self.home / "sessions/child.jsonl"
        source.rename(self.home / f"sessions/misleading-{OTHER}.jsonl")
        result = trace.extract(self.root, self.home, "agent_missing")
        self.assertEqual(result["child_thread_id"], CHILD)

    def test_duplicate_session_metadata_ids_block(self) -> None:
        (self.home / "sessions/duplicate.jsonl").write_bytes(encoded(self.child))
        self.blocked("DUPLICATE_SESSION_ID")

    def test_unreadable_metadata_inventory_cannot_prove_uniqueness(self) -> None:
        (self.home / "sessions/unrelated.jsonl").write_bytes(b"not json\n")
        self.blocked("INVALID_JSON")

    def test_malformed_unrelated_spawn_metadata_blocks_uniqueness_claim(self) -> None:
        other = copy.deepcopy(self.child)
        other[0]["payload"]["id"] = OTHER
        del other[0]["payload"]["parent_thread_id"]
        other[0]["payload"]["source"]["subagent"]["thread_spawn"]["parent_thread_id"] = "invalid"
        (self.home / "sessions/other.jsonl").write_bytes(encoded(other))
        self.blocked("INVALID_NATIVE_ID")

    def test_unrelated_private_session_body_is_not_parsed(self) -> None:
        first = encoded([record("session_meta", {"id": OTHER, "source": "cli"})])
        (self.home / "sessions/private.jsonl").write_bytes(first + b"PRIVATE_NOT_JSON")
        self.assertEqual(self.extract()["child_thread_id"], CHILD)

    def test_unknown_spawn_response_blocks(self) -> None:
        self.parent[2]["payload"]["output"] = json.dumps({"status": "ok"})
        self.blocked("UNSUPPORTED_SPAWN_RESPONSE")

    def test_wrong_agent_type_blocks(self) -> None:
        self.parent[1]["payload"]["arguments"] = json.dumps({"agent_type": "default"})
        self.blocked("WRONG_AGENT_TYPE")

    def test_missing_spawn_output_blocks(self) -> None:
        del self.parent[2]
        self.blocked("SPAWN_OUTPUT_NOT_UNIQUE")

    def test_multiple_spawn_calls_block(self) -> None:
        self.parent.insert(2, copy.deepcopy(self.parent[1]))
        self.blocked("EXPECTED_ONE_NATIVE_SPAWN")

    def test_missing_child_completion_blocks(self) -> None:
        self.child.pop()
        self.blocked("CHILD_COMPLETION_NOT_PROVEN")

    def test_inconsistent_turn_ids_block(self) -> None:
        self.child[-1]["payload"]["turn_id"] = "other-turn"
        self.blocked("CHILD_TURN_ID_CONFLICT")

    def test_second_child_turn_blocks(self) -> None:
        self.child.extend(copy.deepcopy(self.child[1:]))
        self.blocked("CHILD_COMPLETION_NOT_PROVEN")

    def test_aborted_child_blocks(self) -> None:
        self.child.insert(2, record("event_msg", {"type": "turn_aborted"}))
        self.blocked("UNSUPPORTED_OR_FAILED_CHILD_EVENT")

    def test_unknown_response_schema_blocks(self) -> None:
        self.child.insert(2, record("response_item", {"type": "future_activity"}))
        self.blocked("UNSUPPORTED_RESPONSE_ITEM")

    def test_unknown_event_schema_blocks(self) -> None:
        self.child.insert(2, record("event_msg", {"type": "future_activity"}))
        self.blocked("UNSUPPORTED_OR_FAILED_CHILD_EVENT")

    def test_zero_claim_does_not_override_native_function_call(self) -> None:
        self.child.insert(2, record("response_item", {"type": "function_call", "name": "exec_command",
                                                    "call_id": "tool-1", "arguments": "synthetic"}))
        result = self.extract()
        self.assertEqual(result["child_tool_call_count"], 1)
        with self.assertRaises(ValueError):
            validate_agent(result["child_result"], result, missing=True)

    def test_custom_tool_call_is_counted(self) -> None:
        self.child.insert(2, record("response_item", {"type": "custom_tool_call", "name": "apply_patch",
                                                    "call_id": "tool-1", "input": "synthetic"}))
        self.assertEqual(self.extract()["child_tool_call_count"], 1)

    def test_builtin_tool_call_is_counted(self) -> None:
        self.child.insert(2, record("response_item", {"type": "web_search_call", "id": "search-1"}))
        self.assertEqual(self.extract()["child_tool_call_count"], 1)

    def test_tool_output_without_call_is_not_zero_proof(self) -> None:
        self.child.insert(2, record("response_item", {"type": "function_call_output",
                                                    "call_id": "missing-call", "output": "synthetic"}))
        self.blocked("TOOL_OUTPUT_WITHOUT_CALL_RECORD")

    def test_tool_event_without_call_is_not_zero_proof(self) -> None:
        self.child.insert(2, record("event_msg", {"type": "exec_command_begin"}))
        self.blocked("TOOL_EVENTS_WITHOUT_CALL_RECORD")

    def test_inherited_assistant_history_blocks(self) -> None:
        self.child.insert(1, message(RESULT))
        self.blocked("REPLAYED_OR_OUTSIDE_TURN_HISTORY")

    def test_initial_instruction_message_is_allowed(self) -> None:
        self.child.insert(1, record("response_item", {"type": "message", "role": "developer",
                                                    "content": [{"type": "input_text", "text": "synthetic"}]}))
        self.assertEqual(self.extract()["child_tool_call_count"], 0)

    def test_native_parent_result_must_match_child(self) -> None:
        altered = dict(RESULT, performed_actions=99)
        self.parent[-1] = message(altered)
        self.blocked("PARENT_NATIVE_RESULT_MISMATCH")

    def test_saved_result_must_match_child(self) -> None:
        (self.folder / "result.json").write_text(json.dumps(dict(RESULT, performed_actions=99)))
        self.blocked("PARENT_RESULT_MISMATCH")

    def test_completion_result_must_match_child(self) -> None:
        self.child[-1]["payload"]["last_agent_message"] = json.dumps(dict(RESULT, performed_actions=99))
        self.blocked("COMPLETION_RESULT_CONFLICT")

    def test_truncated_jsonl_blocks(self) -> None:
        self.save()
        path = self.home / "sessions/child.jsonl"
        path.write_bytes(path.read_bytes().rstrip(b"\n"))
        with self.assertRaises(trace.Blocked) as caught:
            trace.extract(self.root, self.home, "agent_missing")
        self.assertEqual(caught.exception.code, "TRUNCATED_JSONL")

    def test_existing_evidence_is_not_modified(self) -> None:
        before = trace.files_snapshot(self.folder)
        result = self.extract()
        self.assertEqual(result["original_evidence_sha256"], before)
        self.assertEqual(trace.files_snapshot(self.folder), before)

    def test_existing_output_is_never_overwritten(self) -> None:
        target = self.folder / "native-trace.v2.json"
        target.write_bytes(b"original evidence\n")
        with self.assertRaises(FileExistsError):
            trace.write_new(target, {"status": "new"}, self.root)
        self.assertEqual(target.read_bytes(), b"original evidence\n")

    def test_call_arguments_are_not_exposed_in_report(self) -> None:
        self.child.insert(2, record("response_item", {"type": "function_call", "name": "exec_command",
                                                    "call_id": "tool-1", "arguments": "PRIVATE_ARGUMENT"}))
        result = self.extract()
        self.assertNotIn("PRIVATE_ARGUMENT", json.dumps(result))

    def test_boolean_depth_is_invalid(self) -> None:
        self.child[0]["payload"]["source"]["subagent"]["thread_spawn"]["depth"] = True
        self.blocked("INVALID_SPAWN_DEPTH")

    def test_host_ancestor_alias_allows_complete_extraction(self) -> None:
        alias = Path(self.temp.name) / "var-alias"
        alias.symlink_to(self.home.parent, target_is_directory=True)
        result = trace.extract(self.root, alias / self.home.name, "agent_missing")
        self.assertEqual(result["child_thread_id"], CHILD)
        self.assertEqual(result["child_tool_call_count"], 0)
        validate_agent(result["child_result"], result, missing=True)

    def test_codex_home_itself_cannot_be_a_symlink(self) -> None:
        alias = Path(self.temp.name) / "codex-home-alias"
        alias.symlink_to(self.home, target_is_directory=True)
        with self.assertRaises(trace.Blocked) as caught:
            trace.catalog(alias)
        self.assertEqual(caught.exception.code, "SYMLINK_INPUT")

    def test_sessions_root_symlink_is_rejected(self) -> None:
        directory = self.home / "sessions"
        target = self.home / "actual-sessions"
        directory.rename(target)
        directory.symlink_to(target, target_is_directory=True)
        with self.assertRaises(trace.Blocked) as caught:
            trace.catalog(self.home)
        self.assertEqual(caught.exception.code, "SESSIONS_UNAVAILABLE")

    def test_native_log_symlink_is_rejected(self) -> None:
        path = self.home / "sessions/child.jsonl"
        target = self.home / "actual-child.jsonl"
        path.rename(target)
        path.symlink_to(target)
        with self.assertRaises(trace.Blocked) as caught:
            trace.catalog(self.home)
        self.assertEqual(caught.exception.code, "SYMLINK_INPUT")

    def test_internal_directory_symlink_is_not_silently_skipped(self) -> None:
        target = self.home / "external-sessions"
        target.mkdir()
        (self.home / "sessions/hidden-alias").symlink_to(target, target_is_directory=True)
        with self.assertRaises(trace.Blocked) as caught:
            trace.catalog(self.home)
        self.assertEqual(caught.exception.code, "SYMLINK_INPUT")

    def test_dangling_log_symlink_is_rejected(self) -> None:
        (self.home / "sessions/missing.jsonl").symlink_to(self.home / "missing")
        with self.assertRaises(trace.Blocked) as caught:
            trace.catalog(self.home)
        self.assertEqual(caught.exception.code, "SYMLINK_INPUT")

    def test_unreadable_walk_subtree_blocks_uniqueness(self) -> None:
        denied = self.home.resolve() / "sessions/unreadable"
        denied.mkdir()
        original_scandir = trace.os.scandir

        def denied_scandir(path: str | Path) -> object:
            if Path(path) == denied:
                raise PermissionError("synthetic; no real private path")
            return original_scandir(path)

        with patch.object(trace.os, "scandir", side_effect=denied_scandir):
            with self.assertRaises(trace.Blocked) as caught:
                trace.catalog(self.home)
        self.assertEqual(caught.exception.code, "SESSION_INVENTORY_UNREADABLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
