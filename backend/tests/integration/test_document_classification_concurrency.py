from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy.orm import sessionmaker

from app.models.domain import (
    Clinic,
    ClinicalDocument,
    Institution,
    Patient,
    Role,
    User,
)
from app.services.clinical_documents import (
    DocumentClassificationConflict,
    confirm_document_classification,
)


pytestmark = pytest.mark.integration


def test_postgresql_allows_exactly_one_human_classification_transition(pg_db):
    institution = Institution(code="classification-race", name="Classification race")
    clinic = Clinic(
        name="Classification race clinic",
        institution_key="classification-race",
        institution=institution,
    )
    patient = Patient(first_name="Synthetic", last_name="Classification")
    role = Role(name="classification-race-reviewer")
    first_reviewer = User(
        email="classification-race-1@example.invalid",
        full_name="First reviewer",
        password_hash="not-used",
        role=role,
    )
    second_reviewer = User(
        email="classification-race-2@example.invalid",
        full_name="Second reviewer",
        password_hash="not-used",
        role=role,
    )
    document = ClinicalDocument(
        patient=patient,
        clinic=clinic,
        institution_scope=institution,
        title="Synthetic concurrent classification",
        source_type="uploaded",
        document_type="other",
        record_classification="unclassified",
        review_status="draft",
    )
    pg_db.add_all([document, first_reviewer, second_reviewer])
    pg_db.commit()

    session_factory = sessionmaker(bind=pg_db.get_bind(), expire_on_commit=False)
    barrier = Barrier(2)

    def classify(target: str, reviewer_id: int) -> str:
        with session_factory() as session:
            candidate = session.get(ClinicalDocument, document.id)
            barrier.wait(timeout=10)
            try:
                confirm_document_classification(
                    session,
                    candidate,
                    record_classification=target,
                    reviewer_user_id=reviewer_id,
                    note=f"Synthetic {target} decision",
                )
                session.commit()
                return "committed"
            except DocumentClassificationConflict:
                session.rollback()
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(
            executor.map(
                lambda values: classify(*values),
                [
                    ("clinical", first_reviewer.id),
                    ("financial", second_reviewer.id),
                ],
            )
        )

    assert sorted(outcomes) == ["committed", "conflict"]
    pg_db.expire_all()
    stored = pg_db.get(ClinicalDocument, document.id)
    assert stored.record_classification in {"clinical", "financial"}
    assert stored.is_clinical_record is (stored.record_classification == "clinical")
    assert stored.classification_reviewed_by in {
        first_reviewer.id,
        second_reviewer.id,
    }
