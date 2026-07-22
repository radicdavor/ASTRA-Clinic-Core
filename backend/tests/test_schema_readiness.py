from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool

from app.services.schema_readiness import check_database_schema_readiness, check_database_schema_readiness_connection


def sqlite_engine():
    return create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)


def test_schema_readiness_ready_when_database_revision_matches_head():
    engine = sqlite_engine()
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('head123')"))
        result = check_database_schema_readiness_connection(connection, expected_heads=("head123",))

    assert result.status == "ready"
    assert result.checks == {"database": "reachable", "schema": "up_to_date"}
    assert result.database_revision == "head123"
    assert result.expected_revision == "head123"


def test_schema_readiness_reports_out_of_date_revision():
    engine = sqlite_engine()
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('old123')"))
        result = check_database_schema_readiness_connection(connection, expected_heads=("head123",))

    assert result.status == "not_ready"
    assert result.checks["schema"] == "out_of_date"
    assert result.database_revision == "old123"
    assert result.expected_revision == "head123"


def test_schema_readiness_reports_missing_revision_table_on_existing_schema():
    engine = sqlite_engine()
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE patients (id INTEGER PRIMARY KEY)"))
        result = check_database_schema_readiness_connection(connection, expected_heads=("head123",))

    assert result.status == "not_ready"
    assert result.checks == {"database": "reachable", "schema": "missing_revision_table"}
    assert result.database_revision is None


def test_schema_readiness_reports_empty_database_as_not_migrated():
    engine = sqlite_engine()
    with engine.begin() as connection:
        result = check_database_schema_readiness_connection(connection, expected_heads=("head123",))

    assert result.status == "not_ready"
    assert result.checks == {"database": "reachable", "schema": "not_migrated"}


def test_schema_readiness_reports_multiple_alembic_heads():
    engine = sqlite_engine()
    result = check_database_schema_readiness(
        engine,
        expected_heads_provider=lambda: ("head123", "head456"),
        known_revisions_provider=lambda: frozenset({"head123", "head456"}),
    )

    assert result.status == "not_ready"
    assert result.checks == {"database": "not_checked", "schema": "multiple_heads"}
    assert result.expected_revision == "head123,head456"


def test_schema_readiness_reports_unknown_database_revision():
    engine = sqlite_engine()
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('future123')"))
        result = check_database_schema_readiness_connection(
            connection,
            expected_heads=("head123",),
            known_revisions=frozenset({"head123", "old123"}),
        )

    assert result.status == "not_ready"
    assert result.checks == {"database": "reachable", "schema": "unknown_revision"}
    assert result.database_revision == "future123"


def test_schema_readiness_reports_incomplete_recovery_marker():
    engine = sqlite_engine()
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE _astra_recovery_incomplete (operation_id TEXT NOT NULL)"))
        result = check_database_schema_readiness_connection(connection, expected_heads=("head123",))

    assert result.status == "not_ready"
    assert result.checks == {"database": "reachable", "schema": "recovery_incomplete"}
    assert result.database_revision is None


def test_schema_readiness_reports_multiple_database_revisions():
    engine = sqlite_engine()
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('head123')"))
        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('head456')"))
        result = check_database_schema_readiness_connection(connection, expected_heads=("head123",))

    assert result.status == "not_ready"
    assert result.checks == {"database": "reachable", "schema": "multiple_database_revisions"}
    assert result.database_revision == "head123,head456"


def test_schema_readiness_reports_unreachable_database_without_leaking_credentials(monkeypatch):
    class BrokenEngine:
        def connect(self):
            raise SQLAlchemyError("postgresql://astra:secret@example.invalid/astra")

    result = check_database_schema_readiness(
        BrokenEngine(),
        expected_heads_provider=lambda: ("head123",),
        known_revisions_provider=lambda: frozenset({"head123"}),
    )

    assert result.status == "not_ready"
    assert result.checks == {"database": "unreachable", "schema": "not_checked"}
    assert "secret" not in str(result.to_public_dict())


def test_ready_endpoint_returns_503_when_schema_is_not_ready(client, monkeypatch):
    from app.services.schema_readiness import SchemaReadiness

    monkeypatch.setattr(
        "app.main.check_configured_database_schema_readiness",
        lambda: SchemaReadiness(
            status="not_ready",
            checks={"database": "reachable", "schema": "out_of_date"},
            database_revision="old123",
            expected_revision="head123",
        ),
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["checks"]["schema"] == "out_of_date"
    assert response.json()["checks"]["configuration"] == "valid"


def test_ready_endpoint_returns_503_when_configuration_is_invalid(client, monkeypatch):
    from app.services.schema_readiness import SchemaReadiness

    monkeypatch.setattr(
        "app.main.check_configured_database_schema_readiness",
        lambda: SchemaReadiness(
            status="ready",
            checks={"database": "reachable", "schema": "up_to_date"},
            database_revision="head123",
            expected_revision="head123",
        ),
    )
    monkeypatch.setattr(
        "app.core.config.Settings.production_safety_errors",
        lambda self: ["JWT secret is missing or uses a forbidden development value."],
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["configuration"] == "invalid"
    assert "JWT secret" in response.json()["configuration_errors"][0]


def test_health_endpoint_does_not_fail_when_schema_is_not_ready(client, monkeypatch):
    from app.services.schema_readiness import SchemaReadiness

    monkeypatch.setattr(
        "app.main.check_configured_database_schema_readiness",
        lambda: SchemaReadiness(
            status="not_ready",
            checks={"database": "unreachable", "schema": "not_checked"},
            database_revision=None,
            expected_revision="head123",
        ),
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
