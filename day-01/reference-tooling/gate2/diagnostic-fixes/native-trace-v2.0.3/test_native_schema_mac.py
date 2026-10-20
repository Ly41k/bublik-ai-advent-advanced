"""Synthetic schema fixtures derived from sanitized Mac diagnostics, not native evidence."""

import copy
import json
import unittest

import collect_agent_trace_v2 as t
import test_native_trace_v2 as base


def world() -> dict[str, object]:
    return base.record("world_state", {"full": True, "state": {
        "agents_md": {"directory": "/synthetic", "text": "PRIVATE_INSTRUCTIONS"},
        "apps_instructions": True,
        "collaboration_mode": {"mode": "default", "model": "synthetic", "instructions": "PRIVATE"},
        "context_window_guidance": "synthetic",
        "environments": {"environments": {"local": {"cwd": "/synthetic", "status": "synthetic",
                                                       "shell": "synthetic"}},
                         "current_date": "synthetic", "timezone": "synthetic", "filesystem": "synthetic"},
        "environments_instructions": True, "git_attribution": False,
        "host_skills": {"body": "PRIVATE_SKILL", "includeInstructions": True},
        "managed_developer_instructions": {}, "model": "synthetic", "model_catalog": "synthetic",
        "multi_agent_mode": {"mode": "synthetic", "usage_hint_hash": "synthetic"},
        "multi_agent_usage_hint": "synthetic",
        "permissions": {"instructions": "PRIVATE_PERMISSIONS", "approved_command_prefixes": []},
        "persistent_mode": {}, "plugins_instructions": True,
        "realtime": {"active": False}, "skills": {"includeInstructions": True},
    }})


def settings(thread_id: str) -> dict[str, object]:
    return base.record("event_msg", {"type": "thread_settings_applied", "thread_id": thread_id,
        "thread_settings": {
            "model": "synthetic", "model_provider_id": "synthetic", "approval_policy": "synthetic",
            "approvals_reviewer": "synthetic", "permission_profile": {
                "type": "managed", "file_system": {"type": "restricted", "entries": [
                    {"path": {}, "access": "synthetic"}]}, "network": "synthetic"},
            "cwd": "/synthetic", "runtime_workspace_roots": ["/synthetic"],
            "reasoning_effort": "synthetic", "reasoning_summary": "synthetic",
            "collaboration_mode": {"mode": "synthetic", "settings": {
                "model": "synthetic", "reasoning_effort": "synthetic", "developer_instructions": None}},
            "disabled_plugin_ids": [],
        }})


def token_record(thread_id: str) -> dict[str, object]:
    usage = {key: 0 for key in ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                               "output_tokens", "reasoning_output_tokens", "total_tokens")}
    return base.record("token_usage_record", {"thread_id": thread_id, "turn_id": "child-turn-1",
        "session_id": "synthetic", "root_turn_id": "synthetic", "response_id": "synthetic",
        "usage": dict(usage), "turn_token_usage": dict(usage), "thread_token_usage": dict(usage)})


def completed(item: dict[str, object], thread_id: str = base.CHILD) -> dict[str, object]:
    return base.record("event_msg", {"type": "item_completed", "thread_id": thread_id,
        "turn_id": "child-turn-1", "item": item, "started_at_ms": 0, "completed_at_ms": 1})


def collab() -> dict[str, object]:
    return {"type": "CollabAgentToolCall", "id": "tool-1", "tool": "synthetic", "status": "synthetic",
            "sender_thread_id": base.CHILD, "receiver_thread_ids": [],
            "receiver_agents": [], "agents_states": {}}


def activity() -> dict[str, object]:
    return {"type": "SubAgentActivity", "id": "activity-1", "model": None,
            "reasoning_effort": None, "kind": "synthetic", "agent_thread_id": base.CHILD,
            "agent_path": "synthetic"}


class MacSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = base.NativeTraceTests("test_task_name_only_uses_explicit_native_metadata")
        self.fixture.setUp()
        self.raw_message = base.record("response_item", {"type": "agent_message", "id": "message-1",
            "author": "synthetic", "recipient": "synthetic", "content": [
                {"type": "input_text", "text": "PRIVATE_FRAMING"},
                {"type": "encrypted_content", "encrypted_content": "PRIVATE_ENCRYPTED"}],
            "internal_chat_message_metadata_passthrough": {"turn_id": "child-turn-1", "create_time": 0.0}})
        self.completed = completed({"type": "AgentMessage", "id": "message-1", "phase": "synthetic",
                                    "content": [{"type": "Text", "text": "PRIVATE_RENDERED_TEXT"}]})
        child = self.fixture.child
        initial = [base.record("response_item", {"type": "message", "role": role,
                    "content": [{"type": "input_text", "text": "PRIVATE_INITIAL_CONTEXT"}]})
                   for role in ("developer", "developer", "user", "user")]
        self.world = world()
        self.settings = settings(base.CHILD)
        self.token = token_record(base.CHILD)
        self.fixture.child = [child[0], child[1], *initial, self.world,
            base.record("turn_context", {}), self.settings,
            base.record("inter_agent_communication_metadata", {"trigger_turn": True}),
            self.raw_message, self.completed, child[2], self.token,
            base.record("event_msg", {"type": "token_count"}), child[3]]
        # Exercise the extra parent-only completed item variants without using names as identity.
        self.fixture.parent[1:1] = [world(), settings(base.PARENT), token_record(base.PARENT),
            base.record("inter_agent_communication_metadata", {"trigger_turn": False}),
            completed({"type": "UserMessage", "id": "user-1", "content": [
                {"type": "text", "text": "PRIVATE_USER", "text_elements": []}]}, base.PARENT),
            completed(activity(), base.PARENT), completed(collab(), base.PARENT)]

    def tearDown(self) -> None:
        self.fixture.tearDown()

    def extract(self) -> dict[str, object]:
        return self.fixture.extract()

    def blocked(self, code: str) -> None:
        with self.assertRaises(t.Blocked) as caught:
            self.extract()
        self.assertEqual(caught.exception.code, code)

    def test_observed_mac_child_record_counts_and_zero_tools(self) -> None:
        result = self.extract()
        self.assertEqual(result["child_tool_call_count"], 0)
        self.assertEqual(result["child_completed_item_types"], {"AgentMessage": 1})
        self.assertEqual(result["child_response_item_types"], {"message": 5, "agent_message": 1})
        base.validate_agent(result["child_result"], result, missing=True)

    def test_context_and_encrypted_content_are_never_exposed(self) -> None:
        result = self.extract()
        self.assertNotIn("PRIVATE_", json.dumps(result))
        self.assertIs(result["opaque_agent_content_inspected"], False)

    def test_canonical_assistant_text_alias_keeps_original_json_contract(self) -> None:
        self.fixture.child[12]["payload"]["content"][0]["type"] = "input_text"
        result = self.extract()
        base.validate_agent(result["child_result"], result, missing=True)

    def test_context_delta_is_supported(self) -> None:
        self.fixture.parent.insert(2, base.record("world_state", {
            "full": False, "state": {"environments": {"subagents": "PRIVATE_PATHS"}}}))
        self.assertEqual(self.extract()["child_tool_call_count"], 0)

    def test_unknown_context_state_field_blocks(self) -> None:
        self.world["payload"]["state"]["tool_calls"] = []
        self.blocked("INVALID_NATIVE_SCHEMA")

    def test_world_state_boolean_must_be_boolean(self) -> None:
        self.world["payload"]["full"] = 1
        self.blocked("INVALID_NATIVE_SCHEMA")

    def test_unknown_auxiliary_field_blocks(self) -> None:
        self.token["payload"]["unknown"] = "synthetic"
        self.blocked("INVALID_NATIVE_SCHEMA")

    def test_boolean_usage_counter_blocks(self) -> None:
        self.token["payload"]["usage"]["input_tokens"] = True
        self.blocked("INVALID_NATIVE_SCHEMA")

    def test_negative_usage_counter_blocks(self) -> None:
        self.token["payload"]["usage"]["input_tokens"] = -1
        self.blocked("INVALID_NATIVE_SCHEMA")

    def test_foreign_thread_usage_metadata_blocks(self) -> None:
        self.token["payload"]["thread_id"] = base.OTHER
        self.blocked("FOREIGN_NATIVE_THREAD_METADATA")

    def test_executable_part_in_delivery_envelope_blocks(self) -> None:
        self.raw_message["payload"]["content"].append({"type": "function_call", "name": "synthetic"})
        self.blocked("UNSUPPORTED_AGENT_MESSAGE_PART")

    def test_unknown_delivery_envelope_field_blocks(self) -> None:
        self.raw_message["payload"]["tool_calls"] = []
        self.blocked("INVALID_NATIVE_SCHEMA")

    def test_unknown_completed_tool_item_is_not_ignored(self) -> None:
        self.completed["payload"]["item"] = {"type": "FutureToolCall", "id": "tool-1"}
        self.blocked("UNSUPPORTED_COMPLETED_ITEM")

    def test_completed_collab_tool_without_call_cannot_prove_zero(self) -> None:
        self.completed["payload"]["item"] = collab()
        self.blocked("TOOL_EVENTS_WITHOUT_CALL_RECORD")

    def test_completed_subagent_activity_without_call_cannot_prove_zero(self) -> None:
        self.completed["payload"]["item"] = activity()
        self.blocked("TOOL_EVENTS_WITHOUT_CALL_RECORD")

    def test_tool_call_and_completed_view_are_not_counted_twice(self) -> None:
        self.fixture.child.insert(10, base.record("response_item", {"type": "function_call",
            "name": "synthetic", "call_id": "tool-1", "arguments": "synthetic"}))
        self.completed["payload"]["item"] = collab()
        result = self.extract()
        self.assertEqual(result["child_tool_call_count"], 1)
        with self.assertRaises(ValueError):
            base.validate_agent(result["child_result"], result, missing=True)

    def test_foreign_completed_item_thread_blocks(self) -> None:
        self.completed["payload"]["thread_id"] = base.OTHER
        self.blocked("FOREIGN_NATIVE_THREAD_METADATA")

    def test_foreign_completed_item_turn_blocks(self) -> None:
        self.completed["payload"]["turn_id"] = "foreign-turn"
        self.blocked("COMPLETED_ITEM_TURN_CONFLICT")

    def test_nontext_completed_message_part_blocks(self) -> None:
        self.completed["payload"]["item"]["content"][0]["type"] = "ToolCall"
        self.blocked("UNSUPPORTED_COMPLETED_MESSAGE_PART")

    def test_foreign_settings_thread_blocks(self) -> None:
        self.settings["payload"]["thread_id"] = base.OTHER
        self.blocked("FOREIGN_NATIVE_THREAD_METADATA")

    def test_unknown_settings_field_blocks(self) -> None:
        self.settings["payload"]["thread_settings"]["future_actions"] = []
        self.blocked("INVALID_NATIVE_SCHEMA")

    def test_completed_item_after_turn_end_blocks(self) -> None:
        item = self.fixture.child.pop(11)
        self.fixture.child.append(item)
        self.blocked("COMPLETED_ITEM_OUTSIDE_CHILD_TURN")

    def test_reported_source_hashes_must_match(self) -> None:
        result = self.extract()
        expected = {role: result[role + "_source_sha256"] for role in ("parent", "child")}
        t.verify_reported_sources(result, expected)
        altered = copy.deepcopy(expected)
        altered["child"] = "0" * 64
        with self.assertRaises(t.Blocked) as caught:
            t.verify_reported_sources(result, altered)
        self.assertEqual(caught.exception.code, "REPORTED_NATIVE_SOURCE_CHANGED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
