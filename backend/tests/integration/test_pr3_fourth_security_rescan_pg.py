from sqlalchemy import text

import pytest

from tests.factories import patient


pytestmark = pytest.mark.integration


def test_postgresql_clinical_document_server_default_is_unclassified(pg_db):
    p = patient(pg_db)
    classification = pg_db.execute(
        text(
            """
            INSERT INTO clinical_documents
                (patient_id, source_type, document_type, title)
            VALUES
                (:patient_id, 'external', 'other', 'Fourth rescan default check')
            RETURNING record_classification
            """
        ),
        {"patient_id": p.id},
    ).scalar_one()

    assert classification == "unclassified"
