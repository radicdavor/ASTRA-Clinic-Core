from datetime import UTC, date, datetime, time

import pytest
from fastapi import HTTPException

from app.services.clinic_time import (
    clinic_datetime_to_utc,
    clinic_local_date,
    combine_clinic_date_time,
)


def test_clinic_local_date_is_not_server_or_utc_date():
    instant = datetime(2026, 7, 20, 22, 30, tzinfo=UTC)

    assert clinic_local_date("Europe/Zagreb", instant) == date(2026, 7, 21)
    assert clinic_local_date("America/New_York", instant) == date(2026, 7, 20)


def test_nonexistent_dst_time_is_rejected():
    with pytest.raises(HTTPException) as exc:
        combine_clinic_date_time(date(2026, 3, 29), time(2, 30), "Europe/Zagreb")

    assert exc.value.status_code == 422
    assert "ne postoji" in exc.value.detail


def test_ambiguous_dst_time_is_rejected():
    with pytest.raises(HTTPException) as exc:
        combine_clinic_date_time(date(2026, 10, 25), time(2, 30), "Europe/Zagreb")

    assert exc.value.status_code == 422
    assert "dvosmisleno" in exc.value.detail


def test_normal_clinic_datetime_converts_to_utc():
    local = combine_clinic_date_time(date(2026, 7, 21), time(7, 0), "Europe/Zagreb")

    assert clinic_datetime_to_utc(local) == datetime(2026, 7, 21, 5, 0, tzinfo=UTC)


def test_naive_datetime_is_rejected_for_utc_conversion():
    with pytest.raises(HTTPException) as exc:
        clinic_datetime_to_utc(datetime(2026, 7, 21, 7, 0))

    assert exc.value.status_code == 422
