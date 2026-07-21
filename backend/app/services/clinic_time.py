from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException


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


def _roundtrip_matches(local_dt: datetime) -> bool:
    roundtrip = local_dt.astimezone(UTC).astimezone(local_dt.tzinfo)
    return (
        roundtrip.replace(tzinfo=None) == local_dt.replace(tzinfo=None)
        and roundtrip.fold == local_dt.fold
    )


def combine_clinic_date_time(local_date: date, local_time: time, timezone_name: str | None) -> datetime:
    """Return a clinic-local aware datetime or reject DST-invalid wall times.

    ASTRA stores appointment date/time as clinic-local scheduling fields. When
    those fields are interpreted as an actual instant, nonexistent spring-DST
    wall times and ambiguous autumn-DST wall times must not be silently guessed.
    """

    zone = clinic_zoneinfo(timezone_name)
    naive = datetime.combine(local_date, local_time)
    fold_zero = naive.replace(tzinfo=zone, fold=0)
    fold_one = naive.replace(tzinfo=zone, fold=1)
    fold_zero_valid = _roundtrip_matches(fold_zero)
    fold_one_valid = _roundtrip_matches(fold_one)

    if not fold_zero_valid and not fold_one_valid:
        raise HTTPException(status_code=422, detail="Odabrano lokalno vrijeme ne postoji zbog promjene vremena")
    if fold_zero_valid and fold_one_valid and fold_zero.utcoffset() != fold_one.utcoffset():
        raise HTTPException(status_code=422, detail="Odabrano lokalno vrijeme je dvosmisleno zbog promjene vremena")
    return fold_zero if fold_zero_valid else fold_one


def clinic_datetime_to_utc(local_dt: datetime) -> datetime:
    if local_dt.tzinfo is None:
        raise HTTPException(status_code=422, detail="Lokalni datum i vrijeme moraju imati vremensku zonu")
    return local_dt.astimezone(UTC)
