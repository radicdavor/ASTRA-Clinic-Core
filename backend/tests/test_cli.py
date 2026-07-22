import json

from app import cli
from app.services.schema_readiness import SchemaReadiness


def test_session_cleanup_command_commits_and_reports_deleted_rows(monkeypatch, capsys):
    class FakeSession:
        committed = False

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def commit(self):
            self.committed = True

    session = FakeSession()
    monkeypatch.setattr(cli, "SessionLocal", lambda: session)
    monkeypatch.setattr(cli, "cleanup_expired_sessions", lambda db: 3 if db is session else 0)

    assert cli.main(["session-cleanup"]) == 0
    assert session.committed is True
    assert json.loads(capsys.readouterr().out) == {"deleted_sessions": 3}


def test_schema_status_returns_nonzero_when_database_is_not_ready(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "check_configured_database_schema_readiness",
        lambda: SchemaReadiness(
            status="not_ready",
            checks={"database": "reachable", "schema": "out_of_date"},
            database_revision="0061",
            expected_revision="0062",
        ),
    )

    assert cli.main(["schema-status"]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "not_ready"
    assert output["checks"]["schema"] == "out_of_date"


def test_schema_status_returns_zero_when_database_is_ready(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "check_configured_database_schema_readiness",
        lambda: SchemaReadiness(
            status="ready",
            checks={"database": "reachable", "schema": "up_to_date"},
            database_revision="0062",
            expected_revision="0062",
        ),
    )

    assert cli.main(["schema-status"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ready"
