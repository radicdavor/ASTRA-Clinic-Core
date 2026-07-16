from tests.conftest import login_token
from tests.factories import appointment, clinical_document, patient


def headers(client):
    return {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}


def journey(client, db):
    appt = appointment(db)
    response = client.post("/api/patient-journeys", headers=headers(client), json={"appointment_id": appt.id, "intake_channel": "manual", "initial_stage": "booked"})
    assert response.status_code == 200
    return response.json(), appt


def test_biopsy_pathology_case_is_structured_and_idempotent(client, db, auth_setup):
    visit, _ = journey(client, db)
    activity = visit["activities"][0]
    intervention = client.post(
        f"/api/patient-journeys/{visit['id']}/activities/{activity['id']}/interventions",
        headers=headers(client),
        json={"intervention_type": "biopsy", "anatomical_site": "Sintetički antrum", "description": "Dva sintetička uzorka", "count": 2, "retrieval_status": "collected", "complication": "Nema evidentirane komplikacije"},
    )
    assert intervention.status_code == 201
    payload = {
        "idempotency_key": f"synthetic-pathology-{activity['id']}",
        "external_lab": "Sintetički vanjski laboratorij",
        "specimens": [{
            "specimen_label": "A1",
            "anatomical_site": "Sintetički antrum",
            "specimen_type": "biopsy",
            "source_intervention_id": intervention.json()["id"],
            "container": "Posudica 1",
            "fixation": "Formalin",
            "collection_time": "2026-07-06T09:20:00Z",
        }],
    }
    created = client.post(f"/api/patient-journeys/{visit['id']}/activities/{activity['id']}/pathology-case", headers=headers(client), json=payload)
    repeated = client.post(f"/api/patient-journeys/{visit['id']}/activities/{activity['id']}/pathology-case", headers=headers(client), json=payload)
    assert created.status_code == 201
    assert repeated.status_code == 200
    assert repeated.json()["id"] == created.json()["id"]
    assert created.json()["status"] == "specimens_ready"
    assert created.json()["specimens"][0]["specimen_label"] == "A1"
    sent = client.post(f"/api/pathology-cases/{created.json()['id']}/transition", headers=headers(client), json={"target_status": "sent_to_lab", "external_case_number": "SYN-001"})
    assert sent.status_code == 200 and sent.json()["sent_at"] is not None
    received = client.post(f"/api/pathology-cases/{created.json()['id']}/transition", headers=headers(client), json={"target_status": "received_by_lab"})
    assert received.status_code == 200 and received.json()["lab_received_at"] is not None
    awaiting = client.post(f"/api/pathology-cases/{created.json()['id']}/transition", headers=headers(client), json={"target_status": "awaiting_result"})
    assert awaiting.status_code == 200 and awaiting.json()["status"] == "awaiting_result"


def test_pathology_result_requires_same_patient_and_human_review(client, db, auth_setup):
    visit, appt = journey(client, db)
    activity = visit["activities"][0]
    intervention = client.post(f"/api/patient-journeys/{visit['id']}/activities/{activity['id']}/interventions", headers=headers(client), json={"intervention_type": "polypectomy", "anatomical_site": "Sintetički kolon", "count": 1, "retrieval_status": "retrieved"}).json()
    case = client.post(f"/api/patient-journeys/{visit['id']}/activities/{activity['id']}/pathology-case", headers=headers(client), json={"specimens": [{"specimen_label": "P1", "anatomical_site": "Sintetički kolon", "specimen_type": "polyp", "source_intervention_id": intervention["id"], "collection_time": "2026-07-06T09:20:00Z"}]}).json()

    wrong_document = clinical_document(db, patient_obj=patient(db, "Other", "Patient"))
    wrong = client.post(f"/api/pathology-cases/{case['id']}/result-link", headers=headers(client), json={"clinical_document_id": wrong_document.id})
    assert wrong.status_code == 422

    result = clinical_document(db, patient_obj=appt.patient)
    result.document_type = "pathology"
    linked = client.post(f"/api/pathology-cases/{case['id']}/result-link", headers=headers(client), json={"clinical_document_id": result.id})
    assert linked.status_code == 200
    assert linked.json()["status"] == "clinician_review_required"
    assert linked.json()["patient_notified_at"] is None
    reviewed = client.post(f"/api/pathology-cases/{case['id']}/review", headers=headers(client))
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "clinician_reviewed"
    assert reviewed.json()["reviewed_by"] == auth_setup["admin"].id
    assert reviewed.json()["patient_notified_at"] is None
    ready = client.post(f"/api/pathology-cases/{case['id']}/transition", headers=headers(client), json={"target_status": "patient_notification_ready"})
    assert ready.status_code == 200
    notified = client.post(f"/api/pathology-cases/{case['id']}/transition", headers=headers(client), json={"target_status": "patient_notified"})
    assert notified.status_code == 409


def test_non_specimen_intervention_cannot_create_pathology_case(client, db, auth_setup):
    visit, _ = journey(client, db); activity = visit["activities"][0]
    clip = client.post(f"/api/patient-journeys/{visit['id']}/activities/{activity['id']}/interventions", headers=headers(client), json={"intervention_type": "clip_placement", "anatomical_site": "Sintetičko mjesto", "count": 1}).json()
    response = client.post(f"/api/patient-journeys/{visit['id']}/activities/{activity['id']}/pathology-case", headers=headers(client), json={"specimens": [{"specimen_label": "X1", "anatomical_site": "Sintetičko mjesto", "specimen_type": "other", "source_intervention_id": clip["id"], "collection_time": "2026-07-06T09:20:00Z"}]})
    assert response.status_code == 422
