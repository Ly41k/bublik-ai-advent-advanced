"""Provider boundary and versioned token estimates."""

import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

MODEL = "gpt-6-luna"
MAX_OUTPUT_TOKENS = 128
RATE_VERSION = "gpt-6-luna-standard-text-2026-11-04"
INPUT_RATE = Decimal("0.10")
CACHE_RATE = Decimal("0.01")
OUTPUT_RATE = Decimal("0.50")
MILLION = Decimal(1_000_000)


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int | None = None

    @classmethod
    def from_counts(cls, input_count: object, output_count: object, cached: object):
        if type(input_count) is not int or type(output_count) is not int:
            return None
        if input_count < 0 or output_count < 0:
            return None
        if type(cached) is not int or not 0 <= cached <= input_count:
            cached = None
        return cls(input_count, output_count, cached)

    @property
    def cost(self) -> Decimal:
        cached = self.cached_input_tokens or 0
        return (
            (self.input_tokens - cached) * INPUT_RATE
            + cached * CACHE_RATE
            + self.output_tokens * OUTPUT_RATE
        ) / MILLION


@dataclass(frozen=True)
class Completion:
    text: str
    usage: Usage | None
    provider_request_id: str | None = None
    accepted: bool = True
    rates_applicable: bool = True


class Provider(Protocol):
    def complete(self, prompt: str) -> Completion: ...


class MockProvider:
    def complete(self, prompt: str) -> Completion:
        # Deterministic synthetic counts. Prompt contents never enter the mock response.
        return Completion(
            "Это синтетический ответ шлюза.",
            Usage(len(prompt.split()), 8, 0),
        )


class OpenAIProvider:
    def __init__(self, instructions: str):
        self.instructions = instructions

    def complete(self, prompt: str) -> Completion:
        # Import and create clients only after server-side live admission.
        # The environment can opt in to SDK debug logs at import time.
        for name in ("openai", "httpx", "httpcore"):
            logging.getLogger(name).setLevel(logging.CRITICAL + 1)
        from httpx import Client, Timeout
        from openai import OpenAI

        for name in ("openai", "openai._base_client", "openai._client", "httpx", "httpcore"):
            logging.getLogger(name).setLevel(logging.CRITICAL + 1)
        if any(os.getenv(name) for name in (
            "OPENAI_CUSTOM_HEADERS", "OPENAI_ORG_ID", "OPENAI_PROJECT_ID",
            "OPENAI_ADMIN_KEY", "OPENAI_WEBHOOK_SECRET",
        )):
            raise RuntimeError("Unsupported OpenAI environment override")
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("Live credentials unavailable")
        timeout = Timeout(15.0, connect=5.0)
        with Client(timeout=timeout, trust_env=False, follow_redirects=False) as http_client:
            with OpenAI(
                api_key=key, base_url="https://api.openai.com/v1", max_retries=0,
                timeout=timeout, http_client=http_client,
            ) as client:
                result = client.responses.create(
                    model=MODEL, instructions=self.instructions, input=prompt,
                    max_output_tokens=MAX_OUTPUT_TOKENS, reasoning={"effort": "none"},
                    store=False, service_tier="default", stream=False,
                )
        raw_usage = result.usage
        usage = None
        if raw_usage is not None:
            usage = Usage.from_counts(
                raw_usage.input_tokens, raw_usage.output_tokens,
                getattr(raw_usage.input_tokens_details, "cached_tokens", None),
            )
        rates_applicable = result.model == MODEL and result.service_tier in (None, "default")
        return Completion(
            text=result.output_text, usage=usage, provider_request_id=result._request_id,
            accepted=rates_applicable and result.status == "completed",
            rates_applicable=rates_applicable,
        )


def formatted_cost(cost: Decimal | None) -> str | None:
    return None if cost is None else f"{cost:.8f}"
