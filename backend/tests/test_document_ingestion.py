import pytest

from app.models.domain import AuditLog, ClinicalDocument, DocumentProcessingJob
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
    assert body["record_classification"] == "unclassified"
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
    assert client.get(f"/api/clinical-documents/{document['id']}", headers=headers(client)).status_code == 403
    queued = client.post(f"/api/clinical-documents/{document['id']}/classification", headers=headers(client))
    processed = client.post(
        f"/api/clinical-documents/{document['id']}/classification/{queued.json()['id']}/process",
        headers=headers(client),
    )
    assert processed.status_code == 200
    assert processed.json()["result_metadata_json"]["candidate_label"] == "laboratory"
    db.refresh(db.get(DocumentProcessingJob, processed.json()["id"]).document)
    assert db.get(DocumentProcessingJob, processed.json()["id"]).document.record_classification == "unclassified"
    reviewed = client.post(
        f"/api/clinical-documents/{document['id']}/classification/review",
        headers=headers(client),
        json={"record_classification": "clinical", "note": "Ljudski potvrđen laboratorijski nalaz."},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["record_classification"] == "clinical"
    assert client.get(f"/api/clinical-documents/{document['id']}", headers=headers(client)).status_code == 200
    assert db.query(DocumentProcessingJob).filter_by(clinical_document_id=document["id"], status="completed").count() == 1


def test_nonclinical_classification_keeps_source_out_of_clinical_record(client, db, auth_setup):
    created = journey(client, db)
    document = ingest_text(client, created["id"], "racun.txt").json()

    reviewed = client.post(
        f"/api/clinical-documents/{document['id']}/classification/review",
        headers=headers(client),
        json={"record_classification": "financial", "note": "Administrativni financijski dokument."},
    )

    assert reviewed.status_code == 200
    assert reviewed.json()["record_classification"] == "financial"
    assert reviewed.json()["is_clinical_record"] is False
    assert client.get(f"/api/clinical-documents/{document['id']}", headers=headers(client)).status_code == 403


@pytest.mark.parametrize("target", ["clinical", "administrative", "financial"])
def test_only_unclassified_source_can_receive_human_review_classification(client, db, auth_setup, target):
    created = journey(client, db)
    document = ingest_text(client, created["id"], f"{target}.txt").json()

    first = client.post(
        f"/api/clinical-documents/{document['id']}/classification/review",
        headers=headers(client),
        json={"record_classification": target, "note": "Potvrđena početna klasifikacija."},
    )
    repeated = client.post(
        f"/api/clinical-documents/{document['id']}/classification/review",
        headers=headers(client),
        json={"record_classification": "clinical" if target != "clinical" else "financial"},
    )

    assert first.status_code == 200
    assert repeated.status_code == 409
    assert repeated.json()["detail"] == "Već potvrđena klasifikacija ne može se naknadno mijenjati"
    db.refresh(db.get(ClinicalDocument, document["id"]))
    assert db.get(ClinicalDocument, document["id"]).record_classification == target


def test_classification_requires_reviewer_permission_and_audit_excludes_document_content(client, db, auth_setup):
    created = journey(client, db)
    document = ingest_text(client, created["id"], "restricted.txt").json()

    source = client.get(f"/api/clinical-documents/{document['id']}/source", headers=headers(client))

    denied = client.post(
        f"/api/clinical-documents/{document['id']}/classification/review",
        headers=headers(client, "limited@test.local"),
        json={"record_classification": "clinical"},
    )
    reviewed = client.post(
        f"/api/clinical-documents/{document['id']}/classification/review",
        headers=headers(client),
        json={"record_classification": "clinical"},
    )

    assert source.status_code == 200
    assert denied.status_code == 403
    assert reviewed.status_code == 200
    event = db.query(AuditLog).filter_by(action="document_classification_reviewed", entity_id=document["id"]).one()
    source_event = db.query(AuditLog).filter_by(action="source_document_viewed_for_classification", entity_id=document["id"]).one()
    assert event.before_json["record_classification"] == "unclassified"
    assert event.after_json["record_classification"] == "clinical"
    prohibited = {"raw_text", "ocr_text", "ai_summary", "provenance_json", "attachment_path"}
    assert prohibited.isdisjoint(event.before_json)
    assert prohibited.isdisjoint(event.after_json)
    assert prohibited.isdisjoint(source_event.after_json)


@pytest.mark.parametrize("current", ["clinical", "financial", "private_internal"])
def test_confirmed_or_unknown_classification_cannot_be_promoted_or_reclassified(client, db, auth_setup, current):
    created = journey(client, db)
    document = db.get(ClinicalDocument, ingest_text(client, created["id"], f"{current}.txt").json()["id"])
    document.record_classification = current
    document.is_clinical_record = current == "clinical"
    db.commit()

    response = client.post(
        f"/api/clinical-documents/{document.id}/classification/review",
        headers=headers(client),
        json={"record_classification": "clinical"},
    )

    assert response.status_code == 409
    db.refresh(document)
    assert document.record_classification == current


def test_unclassified_is_not_a_valid_human_review_target(client, db, auth_setup):
    created = journey(client, db)
    document = ingest_text(client, created["id"], "still-unclassified.txt").json()

    response = client.post(
        f"/api/clinical-documents/{document['id']}/classification/review",
        headers=headers(client),
        json={"record_classification": "unclassified"},
    )

    assert response.status_code == 422


def test_ingested_source_path_is_immutable(client, db, auth_setup):
    created = journey(client, db)
    document = ingest_text(client, created["id"]).json()
    assert client.post(
        f"/api/clinical-documents/{document['id']}/classification/review",
        headers=headers(client),
        json={"record_classification": "clinical"},
    ).status_code == 200
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
