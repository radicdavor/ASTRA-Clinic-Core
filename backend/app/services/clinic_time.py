from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_CLINIC_TIMEZONE = "Europe/Zagreb"


def clinic_zoneinfo(timezone_name: str | None) -> ZoneInfo:
    name = timezone_name or DEFAULT_CLINIC_TIMEZONE
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_CLINIC_TIMEZONE)


def utc_now() -> datetime:
    return datetime.now(UTC)


def clinic_local_datetime(timezone_name: str | None, instant: datetime | None = None) -> datetime:
    source = instant or utc_now()
    if source.tzinfo is None:
        source = source.replace(tzinfo=UTC)
    return source.astimezone(clinic_zoneinfo(timezone_name))


def clinic_local_date(timezone_name: str | None, instant: datetime | None = None) -> date:
    return clinic_local_datetime(timezone_name, instant).date()
