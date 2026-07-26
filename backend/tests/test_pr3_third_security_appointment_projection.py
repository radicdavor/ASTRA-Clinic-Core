from datetime import date

from app.auth.dependencies import hash_api_key
from app.models.domain import ApiKey
from app.schemas.common import AppointmentOperationalOut
from tests.conftest import login_token
from tests.factories import appointment


def test_operational_appointment_projection_omits_free_text_fields(db):
    appt = appointment(db)
    appt.notes = "SECRET_APPOINTMENT_NOTE_SENTINEL"
    appt.patient.notes = "SECRET_PATIENT_NOTE_SENTINEL"
    db.flush()

    payload = AppointmentOperationalOut.model_validate(appt).model_dump(mode="json")

    assert "notes" not in payload
    assert "notes" not in payload["patient"]
    serialized = str(payload)
    assert "SECRET_APPOINTMENT_NOTE_SENTINEL" not in serialized
    assert "SECRET_PATIENT_NOTE_SENTINEL" not in serialized


def test_openapi_operational_appointment_contracts_are_narrow(client):
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    forbidden = {"notes", "clinical_notes", "summary", "findings", "therapy", "diagnosis"}

    for name in ("AppointmentOperationalOut", "AppointmentReceptionOut"):
        properties = schemas[name]["properties"]
        assert forbidden.isdisjoint(properties)
        assert "episode" not in properties

    assert forbidden.isdisjoint(schemas["PatientOperationalIdentityOut"]["properties"])
    assert forbidden.isdisjoint(schemas["PatientReceptionIdentityOut"]["properties"])
    assert "price" not in schemas["ServiceOperationalOut"]["properties"]
    assert "email" not in schemas["ProviderOperationalOut"]["properties"]

    paths = client.get("/openapi.json").json()["paths"]
    expected_models = {
        ("post", "/api/appointments"): "AppointmentOperationalOut",
        ("get", "/api/appointments"): "AppointmentOperationalOut",
        ("get", "/api/appointments/{appointment_id}"): "AppointmentOperationalOut",
        ("patch", "/api/appointments/{appointment_id}"): "AppointmentOperationalOut",
        ("get", "/api/schedule/day"): "AppointmentOperationalOut",
        ("post", "/api/intake/web/appointments"): "AppointmentOperationalOut",
        ("post", "/api/ai/appointments/create"): "AppointmentOperationalOut",
        ("get", "/api/ai/today"): "AITodayOut",
        ("get", "/api/reception/day"): "ReceptionSlot",
        ("post", "/api/appointments/{appointment_id}/mark-arrived"): "AppointmentReceptionOut",
        ("post", "/api/appointments/{appointment_id}/start-service"): "AppointmentReceptionOut",
    }
    for (method, path), expected_model in expected_models.items():
        response_schema = paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"]
        assert expected_model in str(response_schema)


def test_reception_and_ai_today_responses_omit_note_sentinels(client, db, auth_setup):
    appt = appointment(db)
    appt.date = date.today()
    appt.notes = "SECRET_APPOINTMENT_NOTE_SENTINEL"
    appt.patient.notes = "SECRET_PATIENT_NOTE_SENTINEL"
    db.flush()

    token = login_token(client, "admin@test.local")
    reception = client.get(
        f"/api/reception/day?date={appt.date.isoformat()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    raw_key = "third_rescan_ai_today_key"
    db.add(
        ApiKey(
            name="Third rescan AI schedule reader",
            key_hash=hash_api_key(raw_key),
            scopes=["ai.free_slots.read"],
            clinic_id=auth_setup["clinic"].id,
            institution_id=auth_setup["clinic"].institution_id,
            active=True,
        )
    )
    db.flush()
    ai_today = client.get("/api/ai/today", headers={"X-ASTRA-API-Key": raw_key})

    assert reception.status_code == 200
    assert ai_today.status_code == 200
    for response in (reception, ai_today):
        assert "SECRET_APPOINTMENT_NOTE_SENTINEL" not in response.text
        assert "SECRET_PATIENT_NOTE_SENTINEL" not in response.text
