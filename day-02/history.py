"""Append-only, hash-chained journal; process lock and crash-aware replay."""

import fcntl
import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from core import encoded, no_links, require, sha


class Journal:
    def __init__(self, path: Path) -> None:
        self.lock = threading.RLock()
        self.path = path.absolute()
        no_links(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        self.stream = os.fdopen(fd, "a+b", buffering=0)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.events = self.read()
            if not self.events:
                self.conversation = str(uuid4())
                self.append("conversation_started", {})
            else:
                self.conversation = self.events[0]["conversation_id"]
        except BaseException:
            self.stream.close()
            raise

    def read(self) -> list[dict]:
        self.stream.seek(0)
        rows, previous = [], "0" * 64
        for raw in self.stream:
            require(raw.endswith(b"\n"), "JOURNAL_TORN_WRITE")
            try:
                value = json.loads(raw)
            except ValueError as error:
                raise ValueError("JOURNAL_CORRUPTED") from error
            checksum = value.pop("sha256", None)
            require(
                value.get("seq") == len(rows) + 1 and value.get("previous") == previous,
                "JOURNAL_SEQUENCE_CORRUPTED",
            )
            require(sha(encoded(value)) == checksum, "JOURNAL_HASH_MISMATCH")
            require(
                not rows or value.get("conversation_id") == rows[0]["conversation_id"],
                "CONVERSATION_MISMATCH",
            )
            previous = checksum
            rows.append({**value, "sha256": checksum})
        return rows

    def append(self, kind: str, data: dict) -> dict:
        with self.lock:
            return self._append(kind, data)

    def _append(self, kind: str, data: dict) -> dict:
        value = {
            "seq": len(self.events) + 1,
            "previous": self.events[-1]["sha256"] if self.events else "0" * 64,
            "timestamp": datetime.now(UTC).isoformat(),
            "conversation_id": self.conversation,
            "kind": kind,
            "data": data,
        }
        value["sha256"] = sha(encoded(value))
        self.stream.write(encoded(value) + b"\n")
        os.fsync(self.stream.fileno())
        self.events.append(value)
        return value

    @property
    def active(self) -> str | None:
        return next(
            (
                e["data"]["profile"]
                for e in reversed(self.events)
                if e["kind"] == "profile_selected"
            ),
            None,
        )

    @property
    def turns(self) -> int:
        return sum(e["kind"] == "turn_reserved" for e in self.events)

    @property
    def unresolved(self) -> bool:
        started = {e["data"]["run_id"] for e in self.events if e["kind"] == "turn_reserved"}
        ended = {e["data"]["run_id"] for e in self.events if e["kind"] == "turn_finished"}
        return bool(started - ended)

    @property
    def failed(self) -> bool:
        return any(
            e["kind"] == "turn_finished" and e["data"]["status"] != "PASS" for e in self.events
        )

    def replay(self, query: str, limit: int = 100_000) -> str:
        messages = [
            {"seq": e["seq"], "role": e["kind"], **e["data"]}
            for e in self.events
            if e["kind"] in {"user_input", "user_message", "assistant_message", "profile_selected"}
        ]
        payload = encoded(
            {
                "history_is_data": True,
                "conversation_id": self.conversation,
                "history": messages,
                "current_request": query,
            }
        ).decode()
        require(len(payload.encode()) <= limit, "CONTEXT_LIMIT_BLOCKED_NO_TRUNCATION")
        return payload

    def close(self) -> None:
        self.stream.close()
