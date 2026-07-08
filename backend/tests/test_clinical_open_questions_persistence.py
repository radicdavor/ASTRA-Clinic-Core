from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.main import app
from app.models.domain import ClinicalEpisode, ClinicalFinding, ClinicalOpenQuestion, ClinicalPlan
from app.schemas.common import CLINICAL_OPEN_QUESTION_STATUSES
from app.services.seed import PERMISSIONS
from tests.factories import patient


FORBIDDEN_COLUMNS = {
    "task_id",
    "outcome_evidence_id",
    "diagnosis_confirmed",
    "treatment_plan",
    "patient_message_id",
    "approval_status",
    "clearance_status",
    "resolved_by_ai",
    "auto_closed_at",
    "patient_notified_at",
    "appointment_status",
}

REQUIRED_COLUMNS = {
    "id",
    "patient_id",
    "finding_id",
    "source_document_id",
    "source_type",
    "source_label",
    "source_reference",
    "question_key",
    "label",
    "status",
    "requires_clinician_review",
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


def question_payload(patient_id: int, **overrides):
    payload = {
        "patient_id": patient_id,
        "finding_id": None,
        "source_document_id": None,
        "source_type": "clinical_document",
        "source_label": "External pathology report",
        "source_reference": "clinical_document:12:key_findings:0",
        "question_key": "question-pathology-follow-up",
        "label": "Does pathology require follow-up decision?",
        "status": "awaiting_review",
        "requires_clinician_review": True,
        "limitations_json": ["Open question is source-linked and requires physician interpretation."],
        "schema_version": "clinical_open_question.v1",
    }
    payload.update(overrides)
    return payload


def insert_question(db, patient_id: int, **overrides):
    question = ClinicalOpenQuestion(**question_payload(patient_id, **overrides))
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def assert_integrity_error(db, patient_id: int | None, **overrides):
    with pytest.raises(IntegrityError):
        insert_question(db, patient_id, **overrides)
    db.rollback()


def test_clinical_open_question_model_and_table_shape_exists():
    assert "clinical_open_questions" in Base.metadata.tables
    assert ClinicalOpenQuestion.__tablename__ == "clinical_open_questions"

    columns = set(ClinicalOpenQuestion.__table__.columns.keys())
    assert REQUIRED_COLUMNS.issubset(columns)
    assert FORBIDDEN_COLUMNS.isdisjoint(columns)


def test_clinical_open_question_allowed_statuses_match_schema_contract(db):
    p = patient(db)

    for status in CLINICAL_OPEN_QUESTION_STATUSES:
        question = insert_question(
            db,
            p.id,
            question_key=f"question-{status}",
            status=status,
        )
        assert question.status == status


def test_clinical_open_question_source_linking_fields_are_required(db):
    p = patient(db)

    assert_integrity_error(db, p.id, source_type="   ")
    assert_integrity_error(db, p.id, source_label="")
    assert_integrity_error(db, p.id, source_reference=" ")
    assert_integrity_error(db, p.id, question_key="")
    assert_integrity_error(db, p.id, label=" ")
    assert_integrity_error(db, p.id, schema_version="")


def test_clinical_open_question_links_to_finding_when_available(db):
    p = patient(db)
    finding = insert_finding(db, p.id)

    question = insert_question(db, p.id, finding_id=finding.id)

    assert question.finding_id == finding.id
    assert question.source_reference == "clinical_document:12:key_findings:0"


def test_clinical_open_question_nullable_relations_require_source_reference(db):
    p = patient(db)

    question = insert_question(db, p.id, finding_id=None, source_document_id=None)

    assert question.finding_id is None
    assert question.source_document_id is None
    assert question.source_reference


def test_clinical_open_question_patient_is_required(db):
    assert_integrity_error(db, None)


def test_clinical_open_question_unsafe_status_is_rejected(db):
    p = patient(db)

    assert_integrity_error(db, p.id, status="resolved_by_ai")


def test_clinical_open_question_closed_status_has_no_workflow_side_effects(db):
    p = patient(db)
    episode_count = db.query(ClinicalEpisode).count()
    plan_count = db.query(ClinicalPlan).count()

    question = insert_question(db, p.id, status="closed_for_now")

    assert question.status == "closed_for_now"
    assert db.query(ClinicalEpisode).count() == episode_count
    assert db.query(ClinicalPlan).count() == plan_count
    assert "tasks" not in Base.metadata.tables
    assert "outcome_evidence" not in Base.metadata.tables
    assert "patient_messages" not in Base.metadata.tables


def test_clinical_open_question_runtime_routes_services_and_permissions_do_not_exist():
    route_paths = {getattr(route, "path", "") for route in app.routes}
    route_methods = {
        (getattr(route, "path", ""), tuple(sorted(getattr(route, "methods", []) or [])))
        for route in app.routes
    }

    assert "/api/open-questions" not in route_paths
    assert "/api/patients/{patient_id}/open-questions" not in route_paths
    assert "/api/findings/{finding_id}/open-questions" not in route_paths
    for path, methods in route_methods:
        if "open-question" in path or "open_questions" in path:
            assert not {"GET", "POST", "PATCH", "PUT", "DELETE"}.intersection(methods)
    assert not Path("app/services/clinical_open_questions.py").exists()
    assert "clinical_open_questions.read" in PERMISSIONS
    assert "clinical_open_questions.write" not in PERMISSIONS
