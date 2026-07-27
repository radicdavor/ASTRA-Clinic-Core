from __future__ import annotations

import re
from uuid import uuid4


REQUEST_ID_MAX_LENGTH = 80
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,80}$")


def normalize_request_id(raw_value: str | None) -> str:
    """Return one safe correlation ID for response, logs, and audit storage."""

    if raw_value is not None and REQUEST_ID_PATTERN.fullmatch(raw_value):
        return raw_value
    return str(uuid4())
