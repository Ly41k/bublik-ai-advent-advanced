"""Validate the sanitized Mac-observed native schema; never expose its contents."""

AUXILIARY_RECORDS = {"world_state", "token_usage_record", "inter_agent_communication_metadata"}
ACTION_ITEMS = {"CollabAgentToolCall", "SubAgentActivity", "CommandExecution"}


class SchemaError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def check(condition: bool, code: str = "INVALID_NATIVE_SCHEMA") -> None:
    if not condition:
        raise SchemaError(code)


def fields(value: object, required: dict[str, type | tuple[type, ...]],
           optional: dict[str, type | tuple[type, ...]] | None = None) -> None:
    check(isinstance(value, dict))
    optional = optional or {}
    check(set(required) <= set(value) <= set(required) | set(optional))
    for key, item in value.items():
        expected = (required | optional)[key]
        types = expected if isinstance(expected, tuple) else (expected,)
        check(type(item) in types)


def string_list(value: list[object]) -> None:
    check(all(isinstance(item, str) for item in value))


def world_state(payload: dict[str, object]) -> None:
    fields(payload, {"full": bool, "state": dict})
    state = payload["state"]
    fields(state, {}, {
        "agents_md": dict, "apps_instructions": bool, "collaboration_mode": dict,
        "context_window_guidance": str, "environments": dict, "environments_instructions": bool,
        "git_attribution": bool, "host_skills": dict, "managed_developer_instructions": dict,
        "model": str, "model_catalog": str, "multi_agent_mode": dict,
        "multi_agent_usage_hint": str, "permissions": dict, "persistent_mode": dict,
        "plugins_instructions": bool, "realtime": dict, "skills": dict,
    })
    schemas = {
        "agents_md": {"directory": str, "text": str},
        "collaboration_mode": {"mode": str, "model": str, "instructions": str},
        "host_skills": {"body": str, "includeInstructions": bool},
        "multi_agent_mode": {"mode": str, "usage_hint_hash": str},
        "permissions": {"instructions": str, "approved_command_prefixes": list},
        "realtime": {"active": bool}, "skills": {"includeInstructions": bool},
    }
    for key, schema in schemas.items():
        if key in state:
            fields(state[key], schema)
    for key in ("managed_developer_instructions", "persistent_mode"):
        if key in state:
            check(state[key] == {}, "UNSUPPORTED_CONTEXT_METADATA")
    if "environments" in state:
        env = state["environments"]
        fields(env, {}, {"environments": dict, "current_date": str, "timezone": str,
                         "filesystem": str, "subagents": str})
        for entry in env.get("environments", {}).values():
            fields(entry, {"cwd": str, "status": str, "shell": str})


def auxiliary(kind: str, payload: dict[str, object], thread_id: str) -> None:
    if kind == "world_state":
        world_state(payload)
    elif kind == "inter_agent_communication_metadata":
        fields(payload, {"trigger_turn": bool})
    elif kind == "token_usage_record":
        fields(payload, {"thread_id": str, "turn_id": str, "session_id": str,
                         "root_turn_id": str, "response_id": str, "usage": dict,
                         "turn_token_usage": dict, "thread_token_usage": dict})
        check(payload["thread_id"] == thread_id, "FOREIGN_NATIVE_THREAD_METADATA")
        usage_schema = {key: int for key in (
            "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
            "output_tokens", "reasoning_output_tokens", "total_tokens")}
        for key in ("usage", "turn_token_usage", "thread_token_usage"):
            fields(payload[key], usage_schema)
            check(all(number >= 0 for number in payload[key].values()))
    else:
        raise SchemaError("UNSUPPORTED_NATIVE_RECORD")


def agent_message(payload: dict[str, object]) -> None:
    """Delivery envelope is not the canonical final result or an executable call."""
    fields(payload, {"type": str, "id": str, "author": str, "recipient": str,
                     "content": list, "internal_chat_message_metadata_passthrough": dict})
    check(payload["type"] == "agent_message")
    check(bool(payload["content"]))
    for part in payload["content"]:
        check(isinstance(part, dict))
        if part.get("type") == "input_text":
            fields(part, {"type": str, "text": str})
        elif part.get("type") == "encrypted_content":
            fields(part, {"type": str, "encrypted_content": str})
        else:
            raise SchemaError("UNSUPPORTED_AGENT_MESSAGE_PART")
    fields(payload["internal_chat_message_metadata_passthrough"],
           {"turn_id": str, "create_time": (int, float)})


def completed_item(item: dict[str, object]) -> str:
    kind = item.get("type")
    if kind == "Reasoning":
        fields(item, {"type": str, "id": str, "summary_text": list, "raw_content": list})
        string_list(item["summary_text"])
        string_list(item["raw_content"])
    elif kind == "CommandExecution":
        fields(item, {"type": str, "id": str, "process_id": str, "command": list,
                      "cwd": str, "parsed_cmd": list, "source": str, "status": str,
                      "aggregated_output": str, "exit_code": int, "duration": dict})
        string_list(item["command"])
        check(bool(item["command"]))
        for parsed in item["parsed_cmd"]:
            fields(parsed, {"type": str, "cmd": str})
            check(parsed["type"] == "unknown", "UNSUPPORTED_PARSED_COMMAND")
        fields(item["duration"], {"secs": int, "nanos": int})
        check(item["duration"]["secs"] >= 0 and 0 <= item["duration"]["nanos"] < 1_000_000_000)
    elif kind == "AgentMessage":
        fields(item, {"type": str, "id": str, "content": list, "phase": str})
        check(bool(item["content"]))
        for part in item["content"]:
            fields(part, {"type": str, "text": str})
            check(part["type"] == "Text", "UNSUPPORTED_COMPLETED_MESSAGE_PART")
    elif kind == "UserMessage":
        fields(item, {"type": str, "id": str, "content": list})
        for part in item["content"]:
            fields(part, {"type": str, "text": str, "text_elements": list})
            check(part["type"] == "text", "UNSUPPORTED_COMPLETED_MESSAGE_PART")
    elif kind == "SubAgentActivity":
        fields(item, {"type": str, "model": (str, type(None)),
                      "reasoning_effort": (str, type(None)), "id": str, "kind": str,
                      "agent_thread_id": str, "agent_path": str})
    elif kind == "CollabAgentToolCall":
        fields(item, {"type": str, "id": str, "tool": str, "status": str,
                      "sender_thread_id": str, "receiver_thread_ids": list,
                      "receiver_agents": list, "agents_states": dict})
        string_list(item["receiver_thread_ids"])
        check(all(isinstance(value, dict) for value in item["receiver_agents"]))
    else:
        raise SchemaError("UNSUPPORTED_COMPLETED_ITEM")
    return kind


def event(payload: dict[str, object], thread_id: str) -> str | None:
    check(payload.get("thread_id") == thread_id, "FOREIGN_NATIVE_THREAD_METADATA")
    if payload.get("type") == "item_completed":
        fields(payload, {"type": str, "thread_id": str, "turn_id": str,
                         "item": dict, "started_at_ms": int, "completed_at_ms": int})
        return completed_item(payload["item"])
    check(payload.get("type") == "thread_settings_applied", "UNSUPPORTED_NATIVE_EVENT")
    fields(payload, {"type": str, "thread_id": str, "thread_settings": dict})
    settings = payload["thread_settings"]
    fields(settings, {"model": str, "model_provider_id": str, "approval_policy": str,
                      "approvals_reviewer": str, "permission_profile": dict, "cwd": str,
                      "runtime_workspace_roots": list, "reasoning_effort": str,
                      "collaboration_mode": dict, "disabled_plugin_ids": list},
           {"reasoning_summary": str})
    string_list(settings["runtime_workspace_roots"])
    string_list(settings["disabled_plugin_ids"])
    profile = settings["permission_profile"]
    fields(profile, {"type": str, "file_system": dict, "network": str})
    check(profile["type"] == "managed")
    fields(profile["file_system"], {"type": str, "entries": list})
    check(profile["file_system"]["type"] == "restricted")
    for entry in profile["file_system"]["entries"]:
        fields(entry, {"path": dict, "access": str})
    mode = settings["collaboration_mode"]
    fields(mode, {"mode": str, "settings": dict})
    fields(mode["settings"], {"model": str, "reasoning_effort": str,
                              "developer_instructions": (str, type(None))})
    return None
