"""Offline synthetic coverage; these fixtures do not prove real Mac execution."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

import collect_agent_trace_v2 as trace
import evaluate_gate2_v203 as aggregate
import test_native_schema_mac as mac
import test_native_trace_v2 as base


def command_item() -> dict[str, object]:
    return {"type": "CommandExecution", "id": "independent-command-item", "process_id": "synthetic",
            "command": ["synthetic-shell", "synthetic-option", "PRIVATE_COMMAND"],
            "cwd": "/synthetic", "parsed_cmd": [{"type": "unknown", "cmd": "PRIVATE_COMMAND"}],
            "source": "synthetic", "status": "completed", "aggregated_output": "PRIVATE_OUTPUT",
            "exit_code": 0, "duration": {"secs": 0, "nanos": 1}}


def reasoning() -> dict[str, object]:
    return {"type": "Reasoning", "id": "reason-1", "summary_text": [], "raw_content": []}


class SuccessSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mac_fixture = mac.MacSchemaTests("test_observed_mac_child_record_counts_and_zero_tools")
        self.mac_fixture.setUp()
        self.fixture = self.mac_fixture.fixture
        old = self.fixture.folder
        self.fixture.folder = old.with_name("agent_success")
        old.rename(self.fixture.folder)
        metadata = json.loads((self.fixture.folder / "metadata.json").read_text())
        metadata["step"] = "agent_success"
        (self.fixture.folder / "metadata.json").write_text(json.dumps(metadata))
        self.result = {"status": "SUCCESS", "result_type": "ArchitectureReport",
            "agent_config_marker": "BUBLIK_ARCHITECTURE_REPORT_V1_20261020", "error_code": None,
            "missing_fields": [], "result": {"summary": "Synthetic fixture; not runtime evidence",
                "files_reviewed": ["src/bublik/application/service.py"], "findings": []},
            "evidence": ["src/bublik/application/service.py#TaskService"], "performed_actions": 1}
        (self.fixture.folder / "result.json").write_text(json.dumps(self.result))
        self.fixture.parent[-1] = base.message(self.result)
        child = self.fixture.child
        child[12] = base.message(self.result)
        child[-1]["payload"]["last_agent_message"] = json.dumps(self.result)
        self.command = command_item()
        self.call = base.record("response_item", {"type": "function_call", "name": "exec",
            "call_id": "model-call-1", "arguments": "PRIVATE_JAVASCRIPT"})
        self.output = base.record("response_item", {"type": "function_call_output",
            "call_id": "model-call-1", "output": "PRIVATE_OUTPUT"})
        child[10:10] = [mac.completed(reasoning()), self.call, self.output, mac.completed(self.command)]
        self.fixture.save()

    def tearDown(self) -> None:
        self.mac_fixture.tearDown()

    def extract(self) -> dict[str, object]:
        self.fixture.save()
        return trace.extract(self.fixture.root, self.fixture.home, "agent_success")

    def blocked(self, code: str) -> None:
        with self.assertRaises(trace.Blocked) as caught:
            self.extract()
        self.assertEqual(caught.exception.code, code)

    def test_actual_shape_with_different_command_id_keeps_one_model_call(self) -> None:
        result = self.extract()
        self.assertEqual(result["child_tool_call_count"], 1)
        audit = result["command_execution_audit"]
        self.assertEqual(audit["completed_command_item_count"], 1)
        self.assertIs(audit["command_item_ids_assumed_to_be_call_ids"], False)
        self.assertIs(audit["command_item_count_added_to_call_count"], False)
        base.validate_agent(result["child_result"], result, missing=False)

    def test_command_arguments_output_and_reasoning_are_not_exposed(self) -> None:
        self.fixture.child[10]["payload"]["item"]["summary_text"] = ["PRIVATE_REASONING"]
        self.assertNotIn("PRIVATE_", json.dumps(self.extract()))

    def test_command_without_native_call_blocks_zero_claim(self) -> None:
        self.fixture.child.remove(self.call)
        self.fixture.child.remove(self.output)
        self.blocked("TOOL_EVENTS_WITHOUT_CALL_RECORD")

    def test_missing_native_call_output_blocks_success(self) -> None:
        self.fixture.child.remove(self.output)
        self.blocked("NATIVE_CALL_COMPLETION_NOT_UNIQUE")

    def test_wrong_native_output_type_does_not_complete_function_call(self) -> None:
        self.output["payload"]["type"] = "custom_tool_call_output"
        self.blocked("NATIVE_CALL_COMPLETION_NOT_UNIQUE")

    def test_ambiguous_native_call_output_blocks_success(self) -> None:
        self.fixture.child.insert(12, copy.deepcopy(self.output))
        self.blocked("NATIVE_CALL_COMPLETION_NOT_UNIQUE")

    def test_failed_command_blocks_success(self) -> None:
        self.command["exit_code"] = 1
        self.blocked("COMMAND_EXECUTION_NOT_SUCCESSFUL")

    def test_incomplete_command_status_blocks_success(self) -> None:
        self.command["status"] = "running"
        self.blocked("COMMAND_EXECUTION_NOT_SUCCESSFUL")

    def test_unknown_parsed_command_variant_blocks(self) -> None:
        self.command["parsed_cmd"][0]["type"] = "future"
        self.blocked("UNSUPPORTED_PARSED_COMMAND")

    def test_extra_command_field_blocks(self) -> None:
        self.command["future_action"] = {}
        self.blocked("INVALID_NATIVE_SCHEMA")

    def test_boolean_exit_code_blocks(self) -> None:
        self.command["exit_code"] = False
        self.blocked("INVALID_NATIVE_SCHEMA")

    def test_executable_object_in_reasoning_blocks(self) -> None:
        self.fixture.child[10]["payload"]["item"]["raw_content"] = [{"type": "function_call"}]
        self.blocked("INVALID_NATIVE_SCHEMA")


class AggregateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / "local-evidence/gate2"
        self.folder.mkdir(parents=True)
        self.write(self.folder / "mac-runtime-probe.json", {"status": "PREFLIGHT_PASS", "os": "Darwin"})
        for step in aggregate.STEPS:
            template = self.root / "gate2/diagnostics" / (step + ".txt")
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("synthetic prompt")
            directory = self.folder / step
            directory.mkdir()
            self.write(directory / "metadata.json", {
                "step": step, "exit_code": 0, "codex": "codex-cli 0.163.0", "python": "3.13.3",
                "os": "Darwin", "sandbox": "workspace-write" if step == "skill" else "read-only",
                "template_sha256": trace.sha(template.read_bytes()), "generation_invocations": 0,
                "diagnostic_parent_invocations": 1})
            self.write(directory / "host-integrity.json", {"status": "PASS", "changed_files": []})
            self.write(directory / "result.json", {})
            (directory / "events.jsonl").write_bytes(base.encoded([
                {"type": "thread.started", "thread_id": base.PARENT}]))
        self.write(self.folder / "skill/result.json", {"status": "PASS",
            "skill_marker": "BUBLIK_QUALITY_GATE_V1_20261020", "runner_exit_code": 0})
        self.skill_events = [
            {"type": "item.completed", "item": {"type": "command_execution",
                "command": "synthetic .agents/skills/quality-gate/SKILL.md", "exit_code": 0}},
            {"type": "item.completed", "item": {"type": "command_execution",
                "command": "synthetic scripts/run_checks.py", "exit_code": 0}},
        ]
        self.save_skill()
        (self.folder / "skill-quality-checks.txt").write_text("38 passed\noverall: PASS\n")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, path: Path, value: dict[str, object]) -> None:
        path.write_text(json.dumps(value))

    def save_skill(self) -> None:
        (self.folder / "skill/events.jsonl").write_bytes(base.encoded(self.skill_events))

    def alter_metadata(self, key: str, value: object) -> None:
        path = self.folder / "agent_success/metadata.json"
        data = json.loads(path.read_text())
        data[key] = value
        self.write(path, data)

    def test_all_four_original_run_records_are_checked(self) -> None:
        self.assertEqual(set(aggregate.validate_runs(self.root)), set(aggregate.STEPS))

    def test_changed_cli_version_blocks(self) -> None:
        self.alter_metadata("codex", "codex-cli other")
        with self.assertRaises(trace.Blocked):
            aggregate.validate_runs(self.root)

    def test_wrong_prompt_hash_blocks(self) -> None:
        self.alter_metadata("template_sha256", "0" * 64)
        with self.assertRaises(trace.Blocked):
            aggregate.validate_runs(self.root)

    def test_generation_invocation_blocks(self) -> None:
        self.alter_metadata("generation_invocations", 1)
        with self.assertRaises(trace.Blocked):
            aggregate.validate_runs(self.root)

    def test_failed_host_integrity_blocks(self) -> None:
        self.write(self.folder / "agent_success/host-integrity.json",
                   {"status": "FAIL", "changed_files": ["synthetic"]})
        with self.assertRaises(trace.Blocked):
            aggregate.validate_runs(self.root)

    def test_original_skill_success_criteria_pass(self) -> None:
        result = aggregate.validate_skill(self.folder, None)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["evidence_method"], "original_cli_events")

    def test_skill_claim_without_runner_execution_blocks(self) -> None:
        self.skill_events.pop()
        self.save_skill()
        with self.assertRaises(trace.Blocked):
            aggregate.validate_skill(self.folder, None)

    def test_skill_claim_without_skill_read_blocks(self) -> None:
        self.skill_events.pop(0)
        self.save_skill()
        with self.assertRaises(trace.Blocked):
            aggregate.validate_skill(self.folder, None)

    def test_skill_runner_nonzero_blocks(self) -> None:
        self.skill_events[-1]["item"]["exit_code"] = 1
        self.save_skill()
        with self.assertRaises(trace.Blocked):
            aggregate.validate_skill(self.folder, None)

    def native_skill_fixture(self) -> dict[str, trace.CatalogEntry]:
        self.skill_events = [{"type": "thread.started", "thread_id": base.PARENT}]
        self.save_skill()
        read_item = command_item()
        read_item["command"] = ["synthetic", ".agents/skills/quality-gate/SKILL.md"]
        run_item = command_item()
        run_item["command"] = ["synthetic", "scripts/run_checks.py"]
        rows = [base.record("session_meta", {"id": base.PARENT, "source": "cli"}),
                mac.completed(read_item, base.PARENT), mac.completed(run_item, base.PARENT)]
        path = self.root / "synthetic-skill-native.jsonl"
        path.write_bytes(base.encoded(rows))
        return {base.PARENT: trace.CatalogEntry(path, base.encoded(rows[:1]), rows[0]["payload"])}

    def test_native_command_transport_satisfies_same_skill_observation(self) -> None:
        index = self.native_skill_fixture()
        result = aggregate.validate_skill(self.folder, index)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["evidence_method"], "cli_and_validated_native_command_events")

    def test_unknown_native_skill_command_schema_blocks(self) -> None:
        index = self.native_skill_fixture()
        path = index[base.PARENT].path
        events = trace.jsonl(path.read_bytes())
        events[1]["payload"]["item"]["future_action"] = {}
        path.write_bytes(base.encoded(events))
        with self.assertRaises(trace.Blocked):
            aggregate.validate_skill(self.folder, index)

    def test_missing_baseline_38_test_evidence_blocks(self) -> None:
        (self.folder / "skill-quality-checks.txt").write_text("overall: PASS\n")
        with self.assertRaises(trace.Blocked):
            aggregate.validate_skill(self.folder, None)

    def startup_fixture(self) -> list[dict[str, object]]:
        return [base.record("session_meta", {"id": base.PARENT, "source": "cli"}),
                base.record("event_msg", {"type": "task_started", "turn_id": "startup-turn"}),
                base.message(aggregate.RULES_RESULT),
                base.record("event_msg", {"type": "task_complete", "turn_id": "startup-turn",
                    "last_agent_message": json.dumps(aggregate.RULES_RESULT)})]

    def test_startup_markers_need_zero_native_calls(self) -> None:
        events = self.startup_fixture()
        aggregate.validate_startup(aggregate.RULES_RESULT, events)
        events.insert(2, base.record("response_item", {"type": "function_call", "name": "exec",
                                                      "call_id": "tool-1", "arguments": "synthetic"}))
        with self.assertRaises(trace.Blocked):
            aggregate.validate_startup(aggregate.RULES_RESULT, events)

    def test_markers_must_equal_actual_native_final_result(self) -> None:
        events = self.startup_fixture()
        events[2] = base.message({"invented": True})
        with self.assertRaises(trace.Blocked):
            aggregate.validate_startup(aggregate.RULES_RESULT, events)

    def test_unsafe_summary_name_never_creates_file(self) -> None:
        self.assertEqual(aggregate.main(["--output-name", "../unsafe.json"]), 1)

    def test_previously_accepted_missing_trace_cannot_be_replaced(self) -> None:
        path = self.folder / "agent_missing/native-trace.v2.0.2.json"
        self.write(path, {"status": "synthetic replacement"})
        with self.assertRaises(trace.Blocked) as caught:
            aggregate.validate_agent_trace(self.root, self.root, "agent_missing", path.name,
                                           {"accepted_missing_trace_sha256": "0" * 64})
        self.assertEqual(caught.exception.code, "ACCEPTED_MISSING_TRACE_CHANGED")


class TraceRevalidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = SuccessSchemaTests("test_actual_shape_with_different_command_id_keeps_one_model_call")
        self.fixture.setUp()
        self.data = self.fixture.extract()
        self.data.update({"agent_contract_status": "PASS", "reported_mac_source_hashes_match": True,
                          "package_verification": {"status": "PASS"}})
        self.path = self.fixture.fixture.folder / "native-trace.v2.0.3.json"
        self.path.write_text(json.dumps(self.data))
        self.overlay = {"reported_mac_success_sources": {
            role: self.data[role + "_source_sha256"] for role in ("parent", "child")}}

    def tearDown(self) -> None:
        self.fixture.tearDown()

    def validate(self) -> dict[str, object]:
        return aggregate.validate_agent_trace(self.fixture.fixture.root, self.fixture.fixture.home,
                                               "agent_success", self.path.name, self.overlay)

    def test_stored_trace_is_rechecked_against_native_log_bytes(self) -> None:
        self.assertEqual(self.validate()["status"], "PASS")

    def test_modified_stored_tool_count_is_rejected(self) -> None:
        self.data["child_tool_call_count"] = 99
        self.path.write_text(json.dumps(self.data))
        with self.assertRaises(trace.Blocked) as caught:
            self.validate()
        self.assertEqual(caught.exception.code, "STORED_TRACE_NATIVE_MISMATCH")

    def test_modified_original_evidence_is_rejected(self) -> None:
        path = self.fixture.fixture.folder / "metadata.json"
        data = json.loads(path.read_text())
        data["extra"] = "modified after extraction"
        path.write_text(json.dumps(data))
        with self.assertRaises(trace.Blocked) as caught:
            self.validate()
        self.assertEqual(caught.exception.code, "ORIGINAL_EVIDENCE_CHANGED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
