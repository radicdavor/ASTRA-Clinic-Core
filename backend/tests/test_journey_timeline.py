from tests.conftest import login_token
from tests.factories import appointment


def headers(client, email="admin@test.local"):
    return {"Authorization": f"Bearer {login_token(client, email)}"}


def create_journey(client, db):
    appt = appointment(db)
    response = client.post(
        "/api/patient-journeys",
        headers=headers(client),
        json={"appointment_id": appt.id, "intake_channel": "manual", "initial_stage": "booked"},
    )
    assert response.status_code == 200
    return response.json()


def ingest(client, journey_id):
    response = client.post(
        f"/api/patient-journeys/{journey_id}/documents/ingest",
        headers=headers(client),
        data={"title": "Sintetički izvor", "document_type": "laboratory", "upload_channel": "staff_upload"},
        files={"file": ("synthetic.txt", b"Synthetic source", "text/plain")},
    )
    assert response.status_code == 200
    return response.json()


def test_timeline_projects_existing_sources_with_provenance(client, db, auth_setup):
    journey = create_journey(client, db)
    document = ingest(client, journey["id"])
    response = client.get(f"/api/patient-journeys/{journey['id']}/timeline", headers=headers(client))
    assert response.status_code == 200
    items = response.json()
    assert any(item["event_type"] == "appointment" for item in items)
    source = next(item for item in items if item["event_type"] == "clinical_document")
    assert source["source_url"] == f"/api/clinical-documents/{document['id']}/source"
    assert source["provenance"]["checksum"] == document["checksum_sha256"]


def test_local_summary_is_labeled_source_linked_and_pending_review(client, db, auth_setup):
    journey = create_journey(client, db)
    document = ingest(client, journey["id"])
    response = client.post(f"/api/patient-journeys/{journey['id']}/summary", headers=headers(client))
    assert response.status_code == 200
    summary = response.json()
    assert summary["provider"] == "local-deterministic-source-index"
    assert summary["model_name"] == "program2-safe-stub-v1"
    assert summary["status"] == "pending_review"
    assert summary["content_json"]["label"].startswith("AI-generirani")
    assert summary["source_refs_json"][0]["document_id"] == document["id"]
    assert summary["facts"][0]["review_status"] == "pending_review"


def test_each_summary_fact_requires_explicit_human_review(client, db, auth_setup):
    journey = create_journey(client, db)
    ingest(client, journey["id"])
    summary = client.post(f"/api/patient-journeys/{journey['id']}/summary", headers=headers(client)).json()
    fact = summary["facts"][0]
    response = client.patch(
        f"/api/patient-journeys/{journey['id']}/summary/{summary['id']}/facts/{fact['id']}",
        headers=headers(client),
        json={"action": "accept"},
    )
    assert response.status_code == 200
    assert response.json()["facts"][0]["review_status"] == "accepted"
    assert response.json()["status"] == "reviewed"


def test_empty_source_set_is_reported_as_missing_not_normal(client, db, auth_setup):
    journey = create_journey(client, db)
    summary = client.post(f"/api/patient-journeys/{journey['id']}/summary", headers=headers(client)).json()
    assert summary["facts"][0]["fact_type"] == "missing_information"
    assert "Nema izvornih dokumenata" in summary["facts"][0]["statement"]


def test_summary_generation_requires_dedicated_permission(client, db, auth_setup):
    journey = create_journey(client, db)
    response = client.post(
        f"/api/patient-journeys/{journey['id']}/summary",
        headers=headers(client, "limited@test.local"),
    )
    assert response.status_code == 403
