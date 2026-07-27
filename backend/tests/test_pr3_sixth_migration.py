import importlib.util
from pathlib import Path

from sqlalchemy import create_engine, text


MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "0069_legacy_document_trust_correction.py"
)


class _DataMigrationOp:
    def __init__(self, connection):
        self.connection = connection

    def add_column(self, *args, **kwargs):
        return None

    def create_foreign_key(self, *args, **kwargs):
        return None

    def create_index(self, *args, **kwargs):
        return None

    def execute(self, statement):
        self.connection.execute(text(statement))


def _migration_module():
    spec = importlib.util.spec_from_file_location("migration_0069", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_legacy_correction_preserves_only_complete_medical_review_provenance(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        for statement in (
            "CREATE TABLE roles (id INTEGER PRIMARY KEY, professional_category TEXT)",
            "CREATE TABLE users (id INTEGER PRIMARY KEY, role_id INTEGER, active BOOLEAN)",
            "CREATE TABLE clinics (id INTEGER PRIMARY KEY, institution_id INTEGER, active BOOLEAN)",
            "CREATE TABLE patient_clinic_associations (patient_id INTEGER, clinic_id INTEGER, active BOOLEAN)",
            """
            CREATE TABLE clinical_documents (
                id INTEGER PRIMARY KEY,
                patient_id INTEGER,
                clinic_id INTEGER,
                institution_id INTEGER,
                is_clinical_record BOOLEAN,
                record_classification TEXT,
                physician_reviewed BOOLEAN,
                reviewed_by INTEGER,
                reviewed_at TEXT,
                classification_reviewed_by INTEGER,
                classification_reviewed_at TEXT
            )
            """,
        ):
            connection.execute(text(statement))
        connection.execute(text("INSERT INTO roles VALUES (1, 'medical_staff')"))
        connection.execute(text("INSERT INTO roles VALUES (2, 'administrative_staff')"))
        connection.execute(text("INSERT INTO users VALUES (1, 1, true)"))
        connection.execute(text("INSERT INTO users VALUES (2, 2, true)"))
        connection.execute(text("INSERT INTO clinics VALUES (1, 1, true)"))
        connection.execute(text("INSERT INTO patient_clinic_associations VALUES (1, 1, true)"))
        connection.execute(text("INSERT INTO patient_clinic_associations VALUES (3, 1, false)"))
        connection.execute(
            text(
                """
                INSERT INTO clinical_documents VALUES
                  (1, 1, 1, 1, true, 'clinical', true, 1, '2026-07-26T10:00:00Z', NULL, NULL),
                  (2, 1, 1, 1, true, 'clinical', false, NULL, NULL, NULL, NULL),
                  (3, 1, 1, 1, true, 'clinical', true, 1, NULL, NULL, NULL),
                  (4, 2, 1, 1, true, 'clinical', true, 1, '2026-07-26T10:00:00Z', NULL, NULL),
                  (5, 3, 1, 1, true, 'clinical', true, 1, '2026-07-26T10:00:00Z', NULL, NULL),
                  (6, 1, 1, 1, true, 'clinical', true, 2, '2026-07-26T10:00:00Z', NULL, NULL)
                """
            )
        )

        module = _migration_module()
        monkeypatch.setattr(module, "op", _DataMigrationOp(connection))
        module.upgrade()

        rows = connection.execute(
            text(
                """
                SELECT id, record_classification, classification_reviewed_by
                FROM clinical_documents
                ORDER BY id
                """
            )
        ).all()

    assert rows == [
        (1, "clinical", 1),
        (2, "unclassified", None),
        (3, "unclassified", None),
        (4, "unclassified", 1),
        (5, "unclassified", 1),
        (6, "unclassified", 2),
    ]


def test_migration_downgrade_does_not_repromote_untrusted_data():
    source = MIGRATION_PATH.read_text(encoding="utf-8")
    downgrade = source.split("def downgrade()", maxsplit=1)[1]
    assert "record_classification = 'clinical'" not in downgrade
    assert "UPDATE clinical_documents" not in downgrade
