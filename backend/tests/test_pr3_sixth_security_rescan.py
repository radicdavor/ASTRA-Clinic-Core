from datetime import datetime, timezone

from app.models.domain import AuditLog, ClinicalDocument, Patient, PatientClinicAssociation
from tests.conftest import login_token


def _headers(client) -> dict[str, str]:
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def test_standalone_document_requires_active_patient_clinic_association(client, db, auth_setup):
    patient = Patient(first_name="Global", last_name="Only")
    db.add(patient)
    db.flush()

    response = client.post(
        "/api/clinical-documents",
        headers=_headers(client),
        json={
            "patient_id": patient.id,
            "clinic_id": auth_setup["clinic"].id,
            "source_type": "external",
            "document_type": "laboratory",
            "title": "Synthetic standalone document",
        },
    )

    assert response.status_code == 404
    assert db.query(ClinicalDocument).filter_by(patient_id=patient.id).count() == 0
    assert db.query(AuditLog).filter_by(entity_type="ClinicalDocument", action="create").count() == 0


def test_inactive_patient_clinic_association_does_not_authorize_upload(client, db, auth_setup):
    patient = Patient(first_name="Inactive", last_name="Association")
    db.add(patient)
    db.flush()
    db.add(
        PatientClinicAssociation(
            patient_id=patient.id,
            clinic_id=auth_setup["clinic"].id,
            active=False,
        )
    )
    db.flush()

    response = client.post(
        "/api/clinical-documents/upload",
        headers=_headers(client),
        json={
            "patient_id": patient.id,
            "clinic_id": auth_setup["clinic"].id,
            "source_type": "uploaded",
            "document_type": "other",
            "title": "Synthetic upload",
            "attachment_name": "synthetic.txt",
        },
    )

    assert response.status_code == 404
    assert db.query(ClinicalDocument).filter_by(patient_id=patient.id).count() == 0


def test_classification_requires_active_patient_clinic_provenance(client, db, auth_setup):
    patient = Patient(first_name="Legacy", last_name="Unbound")
    db.add(patient)
    db.flush()
    document = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=auth_setup["clinic"].id,
        institution_id=auth_setup["clinic"].institution_id,
        source_type="legacy",
        document_type="other",
        title="Synthetic unbound legacy source",
        is_clinical_record=True,
        record_classification="unclassified",
        review_status="draft",
    )
    db.add(document)
    db.flush()

    response = client.post(
        f"/api/clinical-documents/{document.id}/classification/review",
        headers=_headers(client),
        json={"record_classification": "clinical", "note": "Synthetic review"},
    )

    assert response.status_code == 404
    db.refresh(document)
    assert document.record_classification == "unclassified"
    assert document.classification_reviewed_by is None
    assert db.query(AuditLog).filter_by(action="document_classification_reviewed").count() == 0


def test_classification_records_separate_human_review_provenance(client, db, auth_setup):
    patient = Patient(first_name="Bound", last_name="Patient")
    db.add(patient)
    db.flush()
    db.add(
        PatientClinicAssociation(
            patient_id=patient.id,
            clinic_id=auth_setup["clinic"].id,
            active=True,
        )
    )
    document = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=auth_setup["clinic"].id,
        institution_id=auth_setup["clinic"].institution_id,
        source_type="uploaded",
        document_type="other",
        title="Synthetic classified source",
        is_clinical_record=True,
        record_classification="unclassified",
        review_status="draft",
    )
    db.add(document)
    db.flush()

    response = client.post(
        f"/api/clinical-documents/{document.id}/classification/review",
        headers=_headers(client),
        json={"record_classification": "clinical", "note": "Synthetic review"},
    )

    assert response.status_code == 200
    db.refresh(document)
    assert document.classification_reviewed_by == auth_setup["admin"].id
    assert document.classification_reviewed_at is not None
    assert document.physician_reviewed is False


def test_client_generated_ids_never_create_authoritative_access_events(client, db, auth_setup):
    patient = Patient(first_name="Audit", last_name="Target")
    db.add(patient)
    db.flush()
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=auth_setup["clinic"].id, active=True))
    db.flush()

    for suffix in ("one", "two", "three"):
        response = client.post(
            "/api/audit/access-events",
            headers=_headers(client),
            json={
                "action": "patient.viewed",
                "entity_type": "Patient",
                "entity_id": patient.id,
                "surface": "patient_workspace",
                "interaction_id": f"client-assertion-{suffix}",
            },
        )
        assert response.status_code == 409

    assert db.query(AuditLog).filter_by(action="patient.viewed").count() == 0


def test_actual_patient_access_is_server_audited_once_per_request(client, db, auth_setup):
    patient = Patient(first_name="Server", last_name="Audited")
    db.add(patient)
    db.flush()
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=auth_setup["clinic"].id, active=True))
    db.commit()

    for _ in range(2):
        response = client.get(f"/api/patients/{patient.id}", headers=_headers(client))
        assert response.status_code == 200

    events = db.query(AuditLog).filter_by(
        action="patient.viewed",
        entity_type="Patient",
        entity_id=patient.id,
    ).all()
    assert len(events) == 2
    assert all((event.after_json or {}).get("surface") == "patient_workspace" for event in events)


def test_legacy_clinical_intent_is_not_trusted_without_classification_review(db, auth_setup):
    patient = Patient(first_name="Legacy", last_name="Intent")
    db.add(patient)
    db.flush()
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=auth_setup["clinic"].id, active=True))
    document = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=auth_setup["clinic"].id,
        institution_id=auth_setup["clinic"].institution_id,
        source_type="legacy",
        document_type="other",
        title="Synthetic legacy intent",
        is_clinical_record=True,
        record_classification="clinical",
        review_status="reviewed",
        physician_reviewed=True,
        reviewed_by=auth_setup["admin"].id,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(document)
    db.flush()

    assert document.classification_reviewed_by is None
    assert document.record_classification == "clinical"
