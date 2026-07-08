from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.main import app
from app.models.domain import ClinicalEpisode, ClinicalFinding, ClinicalPlan
from app.schemas.common import CLINICAL_FINDING_LIFECYCLE_STATUSES
from app.services.seed import PERMISSIONS
from tests.factories import patient


FORBIDDEN_COLUMNS = {
    "diagnosis_confirmed",
    "treatment_plan",
    "patient_notified",
    "task_id",
    "outcome_evidence_id",
    "approval_status",
    "clearance_status",
    "resolved_by_ai",
    "auto_closed_at",
    "patient_message_id",
    "appointment_status",
}

REQUIRED_COLUMNS = {
    "id",
    "patient_id",
    "source_document_id",
    "source_type",
    "source_label",
    "source_reference",
    "finding_key",
    "label",
    "category",
    "lifecycle_status",
    "requires_review",
    "reviewed_at",
    "reviewed_by_user_id",
    "limitations_json",
    "schema_version",
    "created_at",
    "updated_at",
}


def finding_payload(patient_id: int, **overrides):
    payload = {
        "patient_id": patient_id,
        "source_document_id": None,
        "source_type": "clinical_document",
        "source_label": "External pathology report",
        "source_reference": "clinical_document:12:key_findings:0",
        "finding_key": "pathology-dysplasia-question",
        "label": "Pathology finding requires review",
        "category": "pathology",
        "lifecycle_status": "awaiting_review",
        "requires_review": True,
        "limitations_json": ["Finding is not a diagnosis by itself."],
        "schema_version": "clinical_finding.v1",
    }
    payload.update(overrides)
    return payload


def insert_finding(db, patient_id: int, **overrides):
    finding = ClinicalFinding(**finding_payload(patient_id, **overrides))
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


def assert_integrity_error(db, patient_id: int, **overrides):
    with pytest.raises(IntegrityError):
        insert_finding(db, patient_id, **overrides)
    db.rollback()


def test_clinical_finding_model_and_table_shape_exists():
    assert "clinical_findings" in Base.metadata.tables
    assert ClinicalFinding.__tablename__ == "clinical_findings"

    columns = set(ClinicalFinding.__table__.columns.keys())
    assert REQUIRED_COLUMNS.issubset(columns)
    assert FORBIDDEN_COLUMNS.isdisjoint(columns)


def test_clinical_finding_allowed_statuses_match_schema_contract(db):
    p = patient(db)

    for status in CLINICAL_FINDING_LIFECYCLE_STATUSES:
        finding = insert_finding(
            db,
            p.id,
            finding_key=f"finding-{status}",
            lifecycle_status=status,
        )
        assert finding.lifecycle_status == status


def test_clinical_finding_source_linking_fields_are_required(db):
    p = patient(db)

    assert_integrity_error(db, p.id, source_type="   ")
    assert_integrity_error(db, p.id, source_label="")
    assert_integrity_error(db, p.id, source_reference=" ")
    assert_integrity_error(db, p.id, finding_key="")
    assert_integrity_error(db, p.id, label=" ")
    assert_integrity_error(db, p.id, schema_version="")


def test_clinical_finding_source_document_can_be_nullable_when_reference_exists(db):
    p = patient(db)

    finding = insert_finding(db, p.id, source_document_id=None)

    assert finding.source_document_id is None
    assert finding.source_reference == "clinical_document:12:key_findings:0"


def test_clinical_finding_patient_is_required(db):
    with pytest.raises(IntegrityError):
        insert_finding(db, None)
    db.rollback()


def test_clinical_finding_unsafe_lifecycle_status_is_rejected(db):
    p = patient(db)

    assert_integrity_error(db, p.id, lifecycle_status="diagnosed_by_ai")


def test_clinical_finding_closed_status_has_no_workflow_side_effects(db):
    p = patient(db)
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()

    finding = insert_finding(db, p.id, lifecycle_status="closed_for_now")

    assert finding.lifecycle_status == "closed_for_now"
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert "tasks" not in Base.metadata.tables
    assert "outcome_evidence" not in Base.metadata.tables
    assert "patient_messages" not in Base.metadata.tables


def test_clinical_finding_runtime_routes_services_and_permissions_do_not_exist():
    route_paths = {getattr(route, "path", "") for route in app.routes}
    route_methods = {
        (getattr(route, "path", ""), set(getattr(route, "methods", []) or []))
        for route in app.routes
    }

    assert "/api/findings" not in route_paths
    assert "/api/patients/{patient_id}/findings" not in route_paths
    assert "/api/appointments/{appointment_id}/findings" not in route_paths
    for path, methods in route_methods:
        if path in {
            "/api/patients/{patient_id}/clinical-findings",
            "/api/patients/{patient_id}/clinical-findings/{finding_id}",
        }:
            assert not {"POST", "PATCH", "PUT", "DELETE"}.intersection(methods)
    assert not Path("app/services/clinical_findings.py").exists()
    assert "clinical_findings.write" not in PERMISSIONS
