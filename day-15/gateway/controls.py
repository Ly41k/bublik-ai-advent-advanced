"""Single-process rate limiting, live admission, and metadata-only audit."""

import hashlib
import hmac
import ipaddress
import os
import stat
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .guards import Kind
from .providers import INPUT_RATE, MAX_OUTPUT_TOKENS, MILLION, MODEL, OUTPUT_RATE

POLICY_VERSION = "d15-defender-r1"
ProviderName = Literal["mock", "openai"]
Origin = Literal["MOCK", "OPENAI_API"]
Stage = Literal["validation", "rate", "input", "budget", "provider", "output"]
Decision = Literal["allow", "mask", "block", "reject", "error"]


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    timestamp_utc: datetime
    request_id: UUID
    client_ip_or_hmac: str
    stage: Stage
    decision: Decision
    detected_types: tuple[Kind, ...]
    policy_version: Literal["d15-defender-r1"] = POLICY_VERSION
    provider: ProviderName
    model: Literal["gpt-6-luna"] = MODEL
    origin: Origin
    http_status: Literal[200, 403, 413, 422, 429, 502, 503]
    usage_input_tokens: int | None
    usage_cached_input_tokens: int | None
    usage_output_tokens: int | None
    estimated_cost_usd: str | None
    estimate_status: Literal["KNOWN", "UNKNOWN", "NOT_CALLED"]
    latency_ms: int


class Audit:
    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()

    def _open(self) -> int:
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
        fd = os.open(self.path, flags, 0o600)
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
            os.close(fd)
            raise OSError("Audit sink requires a private regular file")
        return fd

    def check(self) -> None:
        with self.lock:
            fd = self._open()
            try:
                os.fsync(fd)
            finally:
                os.close(fd)

    def append(self, event: AuditEvent) -> None:
        line = (event.model_dump_json() + "\n").encode("utf-8")
        with self.lock:
            fd = self._open()
            try:
                start = os.lseek(fd, 0, os.SEEK_END)
                try:
                    if os.write(fd, line) != len(line):
                        raise OSError("Short audit write")
                    os.fsync(fd)
                except OSError:
                    os.ftruncate(fd, start)
                    raise
            finally:
                os.close(fd)


def client_identity(host: str, hmac_key: bytes) -> tuple[str, str]:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return "unknown", "unknown"
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    address = str(ip)
    if ip.is_loopback:
        return address, address
    pseudonym = hmac.new(hmac_key, address.encode("ascii"), hashlib.sha256).hexdigest()
    return address, f"hmac:{pseudonym}"


class RateLimiter:
    def __init__(self):
        self.windows: dict[str, deque[float]] = {}
        self.last_cleanup: float | None = None
        self.lock = Lock()

    def allow(self, client: str, clock: Callable[[], float]) -> bool:
        with self.lock:
            now = clock()
            cutoff = now - 60
            if self.last_cleanup is None or self.last_cleanup <= cutoff:
                self.windows = {
                    ip: window for ip, window in self.windows.items()
                    if window[-1] > cutoff
                }
                self.last_cleanup = now
            window = self.windows.setdefault(client, deque())
            while window and window[0] <= cutoff:
                window.popleft()
            if len(window) >= 5:
                return False
            window.append(now)
            return True


@dataclass(frozen=True)
class PilotTicket:
    input_bound: int
    reservation: Decimal


class PilotBudget:
    """One process, one live call in flight, up to three attempts including failures."""

    def __init__(self):
        self.lock = Lock()
        self.attempts = 0
        self.total = Decimal(0)
        self.in_flight = False
        self.stopped = False

    def reserve(self, prompt: str, instructions: str) -> PilotTicket | None:
        # Conservative byte-based estimate plus protocol overhead. Reconcile after the call.
        input_bound = len(prompt.encode("utf-8")) + len(instructions.encode("utf-8")) + 1024
        reservation = (input_bound * INPUT_RATE + MAX_OUTPUT_TOKENS * OUTPUT_RATE) / MILLION
        with self.lock:
            if self.stopped or self.in_flight or self.attempts >= 3:
                return None
            if self.total + reservation > Decimal("0.25"):
                self.stopped = True
                return None
            self.in_flight = True
            self.attempts += 1
            return PilotTicket(input_bound, reservation)

    def settle(self, ticket: PilotTicket, cost: Decimal | None, stop: bool) -> None:
        with self.lock:
            self.total += ticket.reservation if cost is None else cost
            self.stopped = stop or cost is None or self.total > Decimal("0.25")
            self.in_flight = False
