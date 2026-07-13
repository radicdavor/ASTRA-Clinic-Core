from app.models.domain import DocumentProcessingJob
from app.services.document_ingestion import EmailIngestionEnvelope, evaluate_email_ingestion
from tests.conftest import login_token
from tests.factories import appointment


def headers(client, email="admin@test.local"):
    return {"Authorization": f"Bearer {login_token(client, email)}"}


def journey(client, db):
    appt = appointment(db)
    response = client.post(
        "/api/patient-journeys",
        headers=headers(client),
        json={"appointment_id": appt.id, "intake_channel": "manual", "initial_stage": "booked"},
    )
    assert response.status_code == 200
    return response.json()


def ingest_text(client, journey_id, filename="synthetic-lab.txt"):
    return client.post(
        f"/api/patient-journeys/{journey_id}/documents/ingest",
        headers=headers(client),
        data={
            "title": "Sintetički laboratorijski nalaz",
            "document_type": "laboratory",
            "upload_channel": "staff_upload",
            "document_date": "2026-07-06",
        },
        files={"file": (filename, b"Synthetic source document\nKKS: test", "text/plain")},
    )


def test_ingestion_preserves_source_metadata_and_download(client, db, auth_setup):
    created = journey(client, db)
    response = ingest_text(client, created["id"])
    assert response.status_code == 200
    body = response.json()
    assert body["lifecycle_status"] == "stored"
    assert body["original_filename"] == "synthetic-lab.txt"
    assert body["mime_type"] == "text/plain"
    assert len(body["checksum_sha256"]) == 64
    assert body["file_size_bytes"] > 0
    source = client.get(f"/api/clinical-documents/{body['id']}/source", headers=headers(client))
    assert source.status_code == 200
    assert source.content == b"Synthetic source document\nKKS: test"


def test_text_demo_ocr_is_explicit_and_source_linked(client, db, auth_setup):
    created = journey(client, db)
    document = ingest_text(client, created["id"]).json()
    queued = client.post(f"/api/clinical-documents/{document['id']}/ocr", headers=headers(client))
    assert queued.status_code == 200
    assert queued.json()["provider"] == "local-demo-text-only"
    processed = client.post(
        f"/api/clinical-documents/{document['id']}/ocr/{queued.json()['id']}/process",
        headers=headers(client),
    )
    assert processed.status_code == 200
    assert processed.json()["status"] == "completed"
    assert processed.json()["result_metadata_json"]["confidence"] == 1.0


def test_image_ocr_fails_instead_of_simulating_success(client, db, auth_setup):
    created = journey(client, db)
    ingested = client.post(
        f"/api/patient-journeys/{created['id']}/documents/ingest",
        headers=headers(client),
        data={"title": "Sintetička slika", "document_type": "other", "upload_channel": "reception_scan"},
        files={"file": ("scan.png", b"not-a-real-image", "image/png")},
    )
    queued = client.post(f"/api/clinical-documents/{ingested.json()['id']}/ocr", headers=headers(client)).json()
    processed = client.post(
        f"/api/clinical-documents/{ingested.json()['id']}/ocr/{queued['id']}/process",
        headers=headers(client),
    )
    assert processed.status_code == 200
    assert processed.json()["status"] == "failed"
    assert "nije konfiguriran" in processed.json()["error_message"]


def test_classification_is_candidate_and_requires_review(client, db, auth_setup):
    created = journey(client, db)
    document = ingest_text(client, created["id"], "laboratorij.txt").json()
    queued = client.post(f"/api/clinical-documents/{document['id']}/classification", headers=headers(client))
    processed = client.post(
        f"/api/clinical-documents/{document['id']}/classification/{queued.json()['id']}/process",
        headers=headers(client),
    )
    assert processed.status_code == 200
    assert processed.json()["result_metadata_json"]["candidate_label"] == "laboratory"
    assert db.query(DocumentProcessingJob).filter_by(clinical_document_id=document["id"], status="completed").count() == 1


def test_ingested_source_path_is_immutable(client, db, auth_setup):
    created = journey(client, db)
    document = ingest_text(client, created["id"]).json()
    response = client.patch(
        f"/api/clinical-documents/{document['id']}",
        headers=headers(client),
        json={"attachment_path": "other/source.txt"},
    )
    assert response.status_code == 409


def test_email_boundary_never_auto_matches_patient():
    result = evaluate_email_ingestion(
        EmailIngestionEnvelope("synthetic-message", "synthetic@example.invalid", ("nalaz.pdf",))
    )
    assert result.status == "manual_review_required"


def test_ingestion_requires_dedicated_permission(client, db, auth_setup):
    created = journey(client, db)
    response = client.post(
        f"/api/patient-journeys/{created['id']}/documents/ingest",
        headers=headers(client, "limited@test.local"),
        data={"title": "Nedopušteno", "document_type": "other", "upload_channel": "staff_upload"},
        files={"file": ("denied.txt", b"denied", "text/plain")},
    )
    assert response.status_code == 403
