from __future__ import annotations

import re

REDACTION = "[REDACTED]"


def redact_text(text: str, patterns: list[str]) -> str:
    redacted = text
    for pattern in patterns:
        redacted = re.sub(pattern, REDACTION, redacted)
    return redacted
