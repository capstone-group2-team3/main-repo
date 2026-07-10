import copy
import re
from typing import Any


SAFETY_NOTICE = "For clinicians only — supports review, not diagnosis or prescribing."

UNSAFE_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bthe patient has\s+([a-z0-9 ,./+-]+)", re.IGNORECASE),
        r"findings may be consistent with \1, pending clinician review",
    ),
    (
        re.compile(r"\bdiagnosed with\s+([a-z0-9 ,./+-]+)", re.IGNORECASE),
        r"findings may be consistent with \1, pending clinician review",
    ),
    (
        re.compile(r"\bdiagnosis is\s+([a-z0-9 ,./+-]+)", re.IGNORECASE),
        r"clinical pattern may suggest \1, requiring clinician review",
    ),
    (
        re.compile(r"\bconfirmed diagnosis\b", re.IGNORECASE),
        "clinical pattern requiring clinician review",
    ),
    (
        re.compile(r"\btreatment plan\b", re.IGNORECASE),
        "clinician review considerations",
    ),
    (
        re.compile(r"\bprescribed\b", re.IGNORECASE),
        "considered according to clinician judgment and local protocols",
    ),
    (
        re.compile(r"\bprescribe\b", re.IGNORECASE),
        "consider according to clinician judgment and local protocols",
    ),
    (
        re.compile(r"\bstart medication\b", re.IGNORECASE),
        "consider medication decisions according to clinician judgment and local protocols",
    ),
    (
        re.compile(r"\bstop medication\b", re.IGNORECASE),
        "review medication decisions according to clinician judgment and local protocols",
    ),
    (
        re.compile(r"\btake medication\b", re.IGNORECASE),
        "use medication only according to clinician judgment and local protocols",
    ),
    (
        re.compile(r"\bdefinitely\b", re.IGNORECASE),
        "may",
    ),
    (
        re.compile(r"\bcure\b", re.IGNORECASE),
        "clinical improvement target",
    ),
    (
        re.compile(r"\bguaranteed\b", re.IGNORECASE),
        "not guaranteed and requiring clinician review",
    ),
]


def sanitize_text(text: str) -> str:
    sanitized = text

    for pattern, replacement in UNSAFE_REPLACEMENTS:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized


def ensure_safety_notice(text: str) -> str:
    if SAFETY_NOTICE in text:
        return text

    if not text.strip():
        return SAFETY_NOTICE

    return f"{text.rstrip()}\n\n{SAFETY_NOTICE}"


def sanitize_dashboard(dashboard_json: dict[str, Any]) -> dict[str, Any]:
    sanitized = _sanitize_value(copy.deepcopy(dashboard_json))

    if not isinstance(sanitized, dict):
        return {"safety_notice": SAFETY_NOTICE}

    sanitized["safety_notice"] = SAFETY_NOTICE
    return sanitized


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)

    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]

    if isinstance(value, dict):
        return {key: _sanitize_value(item) for key, item in value.items()}

    return value
