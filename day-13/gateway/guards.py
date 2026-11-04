"""Deterministic detectors. Matches carry spans and category labels only."""

import base64
import binascii
import re
from dataclasses import dataclass
from enum import StrEnum


class Kind(StrEnum):
    API_KEY = "API_KEY"
    AWS_KEY = "AWS_KEY"
    GITHUB_TOKEN = "GITHUB_TOKEN"
    EMAIL = "EMAIL"
    CARD = "CARD"
    PHONE = "PHONE"
    SYSTEM_PROMPT = "SYSTEM_PROMPT"
    SUSPICIOUS_URL = "SUSPICIOUS_URL"
    DANGEROUS_COMMAND = "DANGEROUS_COMMAND"
    RATE_LIMIT = "RATE_LIMIT"
    PROVIDER_ERROR = "PROVIDER_ERROR"


CREDENTIALS = (
    (Kind.API_KEY, re.compile(
        r"(?<![\w-])(?:sk-proj-" r"abc123|sk-[A-Za-z0-9_-]{16,})(?![A-Za-z0-9_-])"
    )),
    (Kind.AWS_KEY, re.compile(r"(?<!\w)AKIA[A-Z0-9]{16}(?!\w)")),
    (Kind.GITHUB_TOKEN, re.compile(r"(?<!\w)ghp_[A-Za-z0-9]{36,64}(?!\w)")),
)
EMAIL = re.compile(
    r"(?<![\w.+-])[A-Za-z0-9_.%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,63}\b"
)
CARD = re.compile(r"(?<![0-9])(?<![0-9][ -])(?:[0-9][ -]?){12,18}[0-9](?![ -]?[0-9])")
INTERNATIONAL = re.compile(
    r"(?<!\w)\+[1-9](?:[ .()-]{0,3}[0-9]){7,14}(?![ .()-]{0,3}[0-9])"
)
LOCAL_PHONE = re.compile(
    r"(?:\b(?:phone|tel|telephone|телефон|тел)\b\.?\s*[:=]?\s*)"
    r"(\(?[0-9](?:[ .()-]{0,3}[0-9]){6,14})(?![ .()-]{0,3}[0-9])", re.IGNORECASE,
)
BASE64 = re.compile(
    r"(?<![A-Za-z0-9+/_=-])[A-Za-z0-9+/_-]{14,2048}={0,2}(?![A-Za-z0-9+/_=-])"
)
QUOTE = r"""(?:"[^"\n\\]{1,256}"|'[^'\n\\]{1,256}')"""
FRAGMENTS = re.compile(rf"{QUOTE}(?:(?:[ \t]*\+[ \t]*|[ \t]+){QUOTE})+")
QUOTED_VALUE = re.compile(rf"{QUOTE}")

SYSTEM_DUMP = re.compile(
    r"(?:^|[\n>])\s*(?:#{1,6}[ \t]+)?(?:\*\*)?"
    r"(?:system\s+(?:prompt|instructions?)|developer\s+(?:message|instructions?)|"
    r"системн(?:ый\s+промпт|ые\s+инструкции))\s*(?:\*\*)?\s*:"
    r"|<\s*(?:system|developer)(?:_prompt)?\s*>|\[\s*system\s*\]",
    re.IGNORECASE,
)
URL = re.compile(
    r"(?<![\w@])(?:[a-z][a-z0-9+.-]*://[^\s<>]+|//[a-z0-9][^\s<>]+|"
    r"(?:javascript|data|file|mailto|tel|vbscript|about|blob|urn):[^\s<>]+|"
    r"https?%3a%2f%2f[^\s<>]+|"
    r"(?:www\.[a-z0-9-]+(?:\.[a-z0-9-]+)+|"
    r"(?:[a-z0-9-]+\.)+(?:com|net|org|io|dev|edu|gov|co|invalid))"
    r"(?=$|[^\w.-]|\.(?!\w)))",
    re.IGNORECASE,
)
COMMAND = re.compile(
    r"\brm\s+(?:--?[a-z-]+\s+)*-(?:[a-z]*r[a-z]*f|[a-z]*f[a-z]*r)[a-z]*\b"
    r"|\brm\s+(?=[^\r\n;&|]*(?:--recursive\b|-[a-z]*r[a-z]*\b))"
    r"(?=[^\r\n;&|]*(?:--force\b|-[a-z]*f[a-z]*\b))"
    r"|\b(?:curl|wget)\b[^\r\n;|&]*(?:--(?:data(?:-[a-z]+)?|upload-file|post-file|"
    r"post-data|form(?:-string)?|body-(?:data|file))\b|"
    r"\s-(?:[dTF]|X\s*(?:POST|PUT|PATCH)\b))"
    r"|\b(?:curl|wget)\b[^\r\n;|&]*\|\s*(?:\S*/)?(?:ba|z)?sh\b"
    r"|\b(?:ba|z)?sh\s+-c\b[^\r\n]*(?:https?://|(?:curl|wget)\b)"
    r"|\b(?:cat|head|tail|less|more|cp)\s+[^\r\n;|&]*"
    r"(?:\.ssh/(?:id_[\w-]+)|\.aws/credentials|\.netrc\b|(?<![\w.])\.env\b)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Match:
    start: int
    end: int
    kind: Kind
    encoded: bool = False

    @property
    def replacement(self) -> str:
        label = "ENCODED_SECRET" if self.encoded else self.kind.value
        return f"[REDACTED_{label}]"


def valid_card(candidate: str) -> bool:
    digits = [int(char) for char in candidate if char.isascii() and char.isdigit()]
    if len(set(digits)) == 1:
        return False
    total = 0
    for index, digit in enumerate(reversed(digits)):
        doubled = digit * 2 if index % 2 else digit
        total += doubled - 9 if doubled > 9 else doubled
    return total % 10 == 0


def _decode_candidate(candidate: str) -> str | None:
    if not 16 <= len(candidate) <= 2048:
        return None
    padded = candidate if "=" in candidate else candidate + "=" * (-len(candidate) % 4)
    try:
        decoded = base64.b64decode(padded, altchars=b"-_", validate=True)
        encoded = base64.urlsafe_b64encode(decoded).decode("ascii")
        if candidate.translate(str.maketrans("+/", "-_")) not in (encoded, encoded.rstrip("=")):
            return None
        value = decoded.decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None
    if all(char.isprintable() or char in "\r\n\t" for char in value):
        return value
    return None


def _credential_kinds(value: str) -> set[Kind]:
    return {kind for kind, pattern in CREDENTIALS if pattern.search(value)}


def secrets(value: str) -> list[Match]:
    matches = [
        Match(match.start(), match.end(), kind)
        for kind, pattern in (*CREDENTIALS, (Kind.EMAIL, EMAIL), (Kind.PHONE, INTERNATIONAL))
        for match in pattern.finditer(value)
    ]
    matches.extend(
        Match(match.start(), match.end(), Kind.CARD)
        for match in CARD.finditer(value) if valid_card(match.group())
    )
    matches.extend(
        Match(match.start(1), match.end(1), Kind.PHONE)
        for match in LOCAL_PHONE.finditer(value)
    )
    for match in BASE64.finditer(value):
        decoded = _decode_candidate(match.group())
        if decoded is not None:
            matches.extend(
                Match(match.start(), match.end(), kind, encoded=True)
                for kind in _credential_kinds(decoded)
            )
    for match in FRAGMENTS.finditer(value):
        joined = "".join(part.group()[1:-1] for part in QUOTED_VALUE.finditer(match.group()))
        matches.extend(
            Match(match.start(), match.end(), kind) for kind in _credential_kinds(joined)
        )
    return matches


def mask(value: str, matches: list[Match]) -> str:
    groups: list[tuple[int, int, Match]] = []
    for match in sorted(matches, key=lambda item: (item.start, -item.end, not item.encoded, item.kind)):
        if groups and match.start < groups[-1][1]:
            start, end, longest = groups[-1]
            if match.end - match.start > longest.end - longest.start:
                longest = match
            groups[-1] = start, max(end, match.end), longest
        else:
            groups.append((match.start, match.end, match))
    for start, end, longest in reversed(groups):
        value = value[:start] + longest.replacement + value[end:]
    return value


def output_kinds(value: str, instructions: str, canary: str) -> set[Kind]:
    kinds = {match.kind for match in secrets(value)}
    if (canary and canary in value) or instructions in value or SYSTEM_DUMP.search(value):
        kinds.add(Kind.SYSTEM_PROMPT)
    if URL.search(value):
        kinds.add(Kind.SUSPICIOUS_URL)
    if COMMAND.search(value):
        kinds.add(Kind.DANGEROUS_COMMAND)
    return kinds
