from datetime import datetime, timezone

from app.models.domain import AuditLog
from tests.conftest import login_token


def headers(client, auth_setup):
    return {
        "Authorization": f"Bearer {login_token(client, 'admin@test.local')}",
        "X-Clinic-Id": str(auth_setup["clinic"].id),
    }


def test_audit_projection_adds_safe_actor_scope_and_result_without_raw_values(client, db, auth_setup):
    event = AuditLog(
        scope_type="clinic",
        clinic_id=auth_setup["clinic"].id,
        institution_id=auth_setup["clinic"].institution_id,
        actor_type="user",
        actor_user_id=auth_setup["admin"].id,
        action="access_denied",
        entity_type="ClinicalDocument",
        entity_id=44,
        summary="PHI_SUMMARY_SENTINEL",
        before_json={"raw_text": "PHI_BEFORE_SENTINEL"},
        after_json={"reason_code": "foreign_scope", "token": "TOKEN_VALUE_SENTINEL"},
        request_id="safe-request-id",
    )
    db.add(event)
    db.commit()

    response = client.get("/api/audit-log", headers=headers(client, auth_setup))

    assert response.status_code == 200
    payload = response.json()[0]
    assert payload["actor_name"] == auth_setup["admin"].full_name
    assert payload["scope_label"] == auth_setup["clinic"].name
    assert payload["result"] == "denied"
    assert payload["reason_code"] == "foreign_scope"
    assert payload["changed_fields"] == ["raw_text", "reason_code", "token"]
    assert "before_json" not in payload
    assert "after_json" not in payload
    assert "summary" not in payload
    assert "PHI_" not in response.text
    assert "TOKEN_VALUE_SENTINEL" not in response.text


def test_audit_date_filter_uses_inclusive_clinic_local_day(client, db, auth_setup):
    auth_setup["clinic"].timezone = "Europe/Zagreb"
    events = [
        AuditLog(
            scope_type="clinic",
            clinic_id=auth_setup["clinic"].id,
            action="before_local_day",
            entity_type="Patient",
            created_at=datetime(2026, 7, 22, 21, 59, tzinfo=timezone.utc),
        ),
        AuditLog(
            scope_type="clinic",
            clinic_id=auth_setup["clinic"].id,
            action="start_local_day",
            entity_type="Patient",
            created_at=datetime(2026, 7, 22, 22, 1, tzinfo=timezone.utc),
        ),
        AuditLog(
            scope_type="clinic",
            clinic_id=auth_setup["clinic"].id,
            action="end_local_day",
            entity_type="Patient",
            created_at=datetime(2026, 7, 23, 21, 59, tzinfo=timezone.utc),
        ),
        AuditLog(
            scope_type="clinic",
            clinic_id=auth_setup["clinic"].id,
            action="after_local_day",
            entity_type="Patient",
            created_at=datetime(2026, 7, 23, 22, 1, tzinfo=timezone.utc),
        ),
    ]
    db.add_all(events)
    db.commit()

    response = client.get(
        "/api/audit-log?date_from=2026-07-23&date_to=2026-07-23",
        headers=headers(client, auth_setup),
    )

    assert response.status_code == 200
    assert {item["action"] for item in response.json()} == {"start_local_day", "end_local_day"}
