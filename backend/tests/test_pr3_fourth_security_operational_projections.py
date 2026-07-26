from tests.conftest import login_token
from tests.factories import appointment, patient


FORBIDDEN_OPERATIONAL_FIELDS = {
    "notes",
    "clinical_notes",
    "summary",
    "findings",
    "therapy",
    "diagnosis",
}


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def test_journey_projection_omits_global_patient_notes(client, db, auth_setup):
    appt = appointment(db)
    appt.patient.notes = "SECRET_PATIENT_NOTE_SENTINEL"
    db.flush()

    created = client.post(
        "/api/patient-journeys",
        headers=auth_headers(client),
        json={
            "appointment_id": appt.id,
            "intake_channel": "manual",
            "initial_stage": "booked",
        },
    )

    assert created.status_code == 200
    assert "notes" not in created.json()["patient"]
    assert "SECRET_PATIENT_NOTE_SENTINEL" not in created.text


def test_global_search_uses_typed_narrow_projections(client, db, auth_setup):
    searched_patient = patient(db, "SearchSentinel", "Patient")
    searched_patient.notes = "SECRET_PATIENT_NOTE_SENTINEL"
    appt = appointment(db, patient_obj=searched_patient)
    appt.notes = "SECRET_APPOINTMENT_NOTE_SENTINEL"
    db.flush()

    response = client.get(
        "/api/search?q=SearchSentinel",
        headers=auth_headers(client),
    )

    assert response.status_code == 200
    assert response.json()["patients"]
    assert FORBIDDEN_OPERATIONAL_FIELDS.isdisjoint(response.json()["patients"][0])
    assert all(
        FORBIDDEN_OPERATIONAL_FIELDS.isdisjoint(item)
        for item in response.json()["appointments"]
    )
    assert "SECRET_PATIENT_NOTE_SENTINEL" not in response.text
    assert "SECRET_APPOINTMENT_NOTE_SENTINEL" not in response.text


def test_openapi_operational_contract_gate_excludes_free_text(client):
    openapi = client.get("/openapi.json").json()
    schemas = openapi["components"]["schemas"]

    assert FORBIDDEN_OPERATIONAL_FIELDS.isdisjoint(
        schemas["PatientReceptionIdentityOut"]["properties"]
    )
    journey_patient_schema = schemas["JourneyOut"]["properties"]["patient"]
    assert "PatientReceptionIdentityOut" in str(journey_patient_schema)

    search_schema = openapi["paths"]["/api/search"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert "SearchResponse" in str(search_schema)
    for schema_name in (
        "SearchAppointmentOut",
        "PatientIdentityOut",
        "ServiceOperationalOut",
        "DailyDashboardRow",
        "ReceptionSlot",
        "WorkflowTaskOut",
        "WorkflowEpisodeOperationalOut",
    ):
        assert FORBIDDEN_OPERATIONAL_FIELDS.isdisjoint(
            schemas[schema_name]["properties"]
        )

    assert "PatientOperationalIdentityOut" in str(
        schemas["WorkflowTaskOut"]["properties"]["patient"]
    )
    assert "WorkflowEpisodeOperationalOut" in str(
        schemas["WorkflowTaskOut"]["properties"]["episode"]
    )

