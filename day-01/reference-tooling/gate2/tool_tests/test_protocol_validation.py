"""Offline validator unit tests; these never establish native agent integration."""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from evaluate_gate2 import validate_agent  # noqa: E402


def missing_case() -> tuple[dict[str, object], dict[str, object]]:
    result: dict[str, object] = {
        "status": "BLOCKED",
        "result_type": "ArchitectureReport",
        "agent_config_marker": "BUBLIK_ARCHITECTURE_REPORT_V1_20261020",
        "error_code": "MISSING_REQUIRED_INPUT",
        "missing_fields": ["task_spec"],
        "result": None,
        "evidence": [],
        "performed_actions": 0,
    }
    trace: dict[str, object] = {
        "status": "NATIVE_TRACE_EXTRACTED",
        "configured_agent_type": "architecture_report",
        "parent_result_matches_child": True,
        "child_result": copy.deepcopy(result),
        "child_tool_call_count": 0,
    }
    return result, trace


def test_schema_valid_error_can_be_checked_offline() -> None:
    result, trace = missing_case()
    validate_agent(result, trace, missing=True)


def test_self_reported_zero_does_not_override_observed_tool_call() -> None:
    result, trace = missing_case()
    trace["child_tool_call_count"] = 1
    with pytest.raises(ValueError):
        validate_agent(result, trace, missing=True)


def test_no_native_trace_is_rejected() -> None:
    result, _ = missing_case()
    with pytest.raises(ValueError):
        validate_agent(result, {}, missing=True)


def test_parent_rewriting_the_child_result_is_rejected() -> None:
    result, trace = missing_case()
    trace["parent_result_matches_child"] = False
    with pytest.raises(ValueError):
        validate_agent(result, trace, missing=True)


def test_boolean_is_not_accepted_as_an_integer_action_count() -> None:
    result, trace = missing_case()
    result["performed_actions"] = False
    trace["child_result"] = copy.deepcopy(result)
    with pytest.raises(ValueError):
        validate_agent(result, trace, missing=True)
