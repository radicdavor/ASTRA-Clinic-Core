import pytest
from fastapi import HTTPException

from app.auth.dependencies import Actor
from app.services.clinical_readiness_preview import build_clinical_readiness_preview
from tests.conftest import login_token
from tests.factories import appointment


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/appointments/999999/clinical-readiness-preview"),
        ("get", "/api/appointments/999999/clinical-readiness-snapshots"),
        ("get", "/api/appointments/999999/clinical-readiness/acknowledgments"),
        ("post", "/api/appointments/999999/clinical-readiness-snapshots"),
        ("post", "/api/appointments/999999/clinical-readiness-snapshots/999999/supersede"),
    ],
)
def test_non_medical_admin_is_denied_before_clinical_readiness_object_resolution(
    client, db, auth_setup, method, path
):
    auth_setup["admin"].role.professional_category = "administrative"
    db.flush()
    token = login_token(client, "admin@test.local")
    payload = (
        {"reason": "Sigurnosna provjera", "idempotency_key": "readiness-medical-guard"}
        if path.endswith("clinical-readiness-snapshots")
        else {"reason": "Sigurnosna provjera"}
    )

    request_kwargs = {"headers": {"Authorization": f"Bearer {token}"}}
    if method == "post":
        request_kwargs["json"] = payload
    response = getattr(client, method)(path, **request_kwargs)

    assert response.status_code == 403


def test_medical_staff_can_use_clinical_readiness_and_system_readiness_is_separate(
    client, db, auth_setup
):
    appt = appointment(db)
    token = login_token(client, "admin@test.local")
    headers = {"Authorization": f"Bearer {token}"}

    clinical = client.get(
        f"/api/appointments/{appt.id}/clinical-readiness-preview",
        headers=headers,
    )
    system = client.get("/api/readiness", headers=headers)

    assert clinical.status_code == 200
    assert system.status_code == 200


def test_clinical_readiness_service_rejects_non_medical_actor(db, auth_setup):
    appt = appointment(db)
    auth_setup["admin"].role.professional_category = "administrative"
    db.flush()

    with pytest.raises(HTTPException) as exc_info:
        build_clinical_readiness_preview(
            db,
            appt,
            actor=Actor(actor_type="user", user=auth_setup["admin"]),
        )

    assert exc_info.value.status_code == 403
