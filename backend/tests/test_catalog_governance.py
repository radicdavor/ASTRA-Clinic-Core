from app.models.domain import ClinicalFormDefinition, ClinicalFormVersion, PatientJourney, ServiceFormBinding
from tests.conftest import login_token
from tests.factories import appointment


def headers(client):
    return {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}


def test_governed_form_definition_publish_and_explicit_binding(client, db, auth_setup):
    appt = appointment(db)
    created = client.post("/api/clinical-forms/definitions", headers=headers(client), json={
        "form_key": "governed-test", "name": "Kontrolirani obrazac", "specialty_key": "general", "activity_kind": "specialist_consultation",
        "sections_json": [{"section_key": "main", "fields": [{"field_key": "opinion", "label": "Mišljenje", "type": "long_text", "required": True}]}],
        "output_document_type": "specialist_report",
    })
    assert created.status_code == 201
    definition = db.query(ClinicalFormDefinition).filter_by(form_key="governed-test").one()
    version = db.query(ClinicalFormVersion).filter_by(definition_id=definition.id).one()
    assert version.status == "draft"
    assert client.post(f"/api/clinical-form-bindings", headers=headers(client), json={"form_version_id": version.id, "service_id": appt.service_id}).status_code == 409
    published = client.post(f"/api/clinical-form-versions/{version.id}/publish", headers=headers(client))
    assert published.status_code == 200 and published.json()["status"] == "published"
    binding = client.post("/api/clinical-form-bindings", headers=headers(client), json={"form_version_id": version.id, "service_id": appt.service_id})
    assert binding.status_code == 201
    assert db.query(ServiceFormBinding).filter_by(service_id=appt.service_id, form_version_id=version.id).count() == 1


def test_published_package_materializes_multiple_activities_in_one_journey(client, db, auth_setup):
    appt = appointment(db)
    visit = client.post("/api/patient-journeys", headers=headers(client), json={"appointment_id": appt.id, "intake_channel": "manual", "initial_stage": "booked"}).json()
    package = client.post("/api/service-packages", headers=headers(client), json={"package_key": "two-step-test", "name": "Dvije sintetičke usluge", "specialty_key": "general"}).json()
    version = client.post(f"/api/service-packages/{package['id']}/versions", headers=headers(client), json={"items": [
        {"service_id": appt.service_id, "activity_key": "package-one", "activity_kind": "specialist_consultation", "specialty_key": "general", "sequence": 1, "default_duration_minutes": 30},
        {"service_id": appt.service_id, "activity_key": "package-two", "activity_kind": "specialist_consultation", "specialty_key": "general", "sequence": 2, "default_duration_minutes": 30},
    ]}).json()
    assert client.post(f"/api/service-package-versions/{version['id']}/publish", headers=headers(client)).status_code == 200
    items = client.get("/api/service-packages", headers=headers(client)).json()[0]["versions"][0]["items"]
    materialized = client.post(f"/api/patient-journeys/{visit['id']}/packages/{version['id']}/materialize", headers=headers(client), json={"assignments": [
        {"package_item_id": items[0]["id"], "date": "2026-07-06", "start_time": "10:00", "end_time": "10:30", "provider_id": appt.provider_id, "room_id": appt.room_id},
        {"package_item_id": items[1]["id"], "date": "2026-07-06", "start_time": "10:30", "end_time": "11:00", "provider_id": appt.provider_id, "room_id": appt.room_id},
    ]})
    assert materialized.status_code == 200, materialized.text
    assert len(materialized.json()) == 2
    activities = client.get(f"/api/patient-journeys/{visit['id']}/activities", headers=headers(client)).json()
    assert len(activities) == 3
    assert {item["activity_key"] for item in activities} >= {"primary", "package-one", "package-two"}


def test_package_preview_booking_and_retry_create_one_coordinated_arrival(client, db, auth_setup):
    appt = appointment(db)
    package = client.post("/api/service-packages", headers=headers(client), json={"package_key": "gastro-three-step-test", "name": "Sintetički gastro paket", "description": "Prvi pregled, gastroskopija i kolonoskopija", "specialty_key": "gastroenterology"}).json()
    version = client.post(f"/api/service-packages/{package['id']}/versions", headers=headers(client), json={"items": [
        {"service_id": appt.service_id, "activity_key": "first-consultation", "activity_kind": "specialist_consultation", "specialty_key": "gastroenterology", "sequence": 1, "default_duration_minutes": 30, "preparation_requirements_json": []},
        {"service_id": appt.service_id, "activity_key": "gastroscopy", "activity_kind": "gastroscopy", "specialty_key": "gastroenterology", "sequence": 2, "default_duration_minutes": 30, "preparation_requirements_json": [{"requirement_key": "fasting", "label": "Natašte", "patient_instruction": "Ne jesti prema odobrenoj uputi.", "category": "fasting"}]},
        {"service_id": appt.service_id, "activity_key": "colonoscopy", "activity_kind": "colonoscopy", "specialty_key": "gastroenterology", "sequence": 3, "default_duration_minutes": 30, "preparation_requirements_json": [{"requirement_key": "bowel_preparation", "label": "Priprema crijeva", "patient_instruction": "Provesti odobrenu pripremu crijeva.", "category": "bowel_preparation"}]},
    ]}).json()
    assert client.post(f"/api/service-package-versions/{version['id']}/publish", headers=headers(client)).status_code == 200
    listed = next(item for item in client.get("/api/service-packages", headers=headers(client)).json() if item["id"] == package["id"])
    items = listed["versions"][0]["items"]
    assignments = [
        {"package_item_id": items[0]["id"], "date": "2026-07-07", "start_time": "08:00", "end_time": "08:30", "provider_id": appt.provider_id, "room_id": appt.room_id},
        {"package_item_id": items[1]["id"], "date": "2026-07-07", "start_time": "08:40", "end_time": "09:10", "provider_id": appt.provider_id, "room_id": appt.room_id},
        {"package_item_id": items[2]["id"], "date": "2026-07-07", "start_time": "09:20", "end_time": "09:50", "provider_id": appt.provider_id, "room_id": appt.room_id},
    ]
    preview = client.post(f"/api/service-package-versions/{version['id']}/schedule-preview", headers=headers(client), json={"patient_id": appt.patient_id, "assignments": assignments})
    assert preview.status_code == 200, preview.text
    assert preview.json()["valid"] is True, preview.json()
    assert preview.json()["total_visit_duration_minutes"] == 110
    assert db.query(PatientJourney).count() == 0

    payload = {"patient_id": appt.patient_id, "idempotency_key": "synthetic-gastro-package-001", "assignments": assignments}
    booked = client.post(f"/api/service-package-versions/{version['id']}/book", headers=headers(client), json=payload)
    repeated = client.post(f"/api/service-package-versions/{version['id']}/book", headers=headers(client), json=payload)
    assert booked.status_code == 201, booked.text
    assert repeated.status_code == 201
    assert repeated.json()["journey_id"] == booked.json()["journey_id"]
    detail = client.get(f"/api/patient-journeys/{booked.json()['journey_id']}", headers=headers(client)).json()
    assert len(detail["activities"]) == 3
    combined = client.get(f"/api/patient-journeys/{booked.json()['journey_id']}/activity-preparation", headers=headers(client)).json()
    assert {item["requirement_key"] for item in combined["requirements"]} == {"fasting", "bowel_preparation"}
