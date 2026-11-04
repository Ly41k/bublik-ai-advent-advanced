"""Replay the four documented HTTP outcomes with the default MockProvider."""

import json
import socket
import sys
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from gateway.app import Settings, create_app
from .synthetic import CLEAN, SENSITIVE, SHORT_KEY


def main():
    if len(sys.argv) > 2:
        raise SystemExit("Usage: python -m tests.smoke [audit-excerpt.jsonl]")
    outbound_attempts = []

    def deny(*args, **kwargs):
        outbound_attempts.append(1)
        raise RuntimeError("Offline socket guard")

    with ExitStack() as stack:
        directory = stack.enter_context(TemporaryDirectory())
        for attribute in ("connect", "connect_ex", "sendto"):
            stack.enter_context(patch.object(socket.socket, attribute, deny))
        stack.enter_context(patch.object(socket, "getaddrinfo", deny))
        path = Path(directory) / "audit.jsonl"
        client = stack.enter_context(TestClient(
            create_app(Settings(audit_path=path)), client=("127.0.0.1", 50000),
        ))

        def post(prompt, mode="block"):
            return client.post("/v1/chat", json={"prompt": prompt, "mode": mode})

        clean, blocked, masked = post(CLEAN), post(SHORT_KEY), post(SHORT_KEY, "mask")
        filler = (post(CLEAN), post(CLEAN))
        limited = post(CLEAN)
        cases = {"clean": clean, "blocked": blocked, "masked": masked, "rate_limited": limited}
        actual = {label: response.status_code for label, response in cases.items()}
        if list(actual.values()) != [200, 403, 200, 429] or any(r.status_code != 200 for r in filler):
            raise SystemExit("Unexpected smoke status")
        if blocked.json().get("stage") != "input" or masked.json()["input_guard"]["action"] != "mask":
            raise SystemExit("Unexpected guard decision")
        if clean.json().get("origin") != "MOCK" or masked.json().get("origin") != "MOCK":
            raise SystemExit("Unexpected provider origin")
        lines = path.read_text().splitlines()
        bodies = "".join(response.text for response in cases.values())
        if outbound_attempts or any(value in bodies + "\n".join(lines) for value in SENSITIVE):
            raise SystemExit("Offline or redaction invariant failed")
        ids = {response.json()["request_id"] for response in cases.values()}
        excerpt = [line for line in lines if json.loads(line)["request_id"] in ids]
        if len(lines) != 6 or len(excerpt) != 4:
            raise SystemExit("Unexpected audit record count")
        if len(sys.argv) == 2:
            Path(sys.argv[1]).write_text("\n".join(excerpt) + "\n", encoding="utf-8")
        print(json.dumps({**actual, "origin": "MOCK", "outbound_socket_attempts": 0}))


if __name__ == "__main__":
    main()
