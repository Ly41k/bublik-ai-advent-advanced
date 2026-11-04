import socket

import pytest

from .synthetic import SENSITIVE


def check(condition, message):
    # Assertions involving synthetic secrets must never print values or diffs.
    if not condition:
        pytest.fail(message, pytrace=False)


@pytest.fixture(autouse=True)
def offline_and_audit_scan(monkeypatch, tmp_path, caplog):
    attempts = []

    def no_network(*args, **kwargs):
        attempts.append(1)
        raise AssertionError("Unexpected outbound socket operation")

    for attr in ("connect", "connect_ex", "sendto"):
        monkeypatch.setattr(socket.socket, attr, no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)
    for name in ("OPENAI_API_KEY", "OPENAI_CUSTOM_HEADERS", "OPENAI_ORG_ID",
                 "OPENAI_PROJECT_ID", "OPENAI_ADMIN_KEY", "OPENAI_WEBHOOK_SECRET"):
        monkeypatch.delenv(name, raising=False)
    yield
    check(not attempts, "Network attempt detected")
    for path in tmp_path.rglob("*.jsonl"):
        if path.is_file():
            contents = path.read_text(encoding="utf-8")
            check(not any(value in contents for value in SENSITIVE), "Audit fixture leak")
    check(not any(value in caplog.text for value in SENSITIVE), "Application logging fixture leak")
