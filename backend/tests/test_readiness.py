from app.models.domain import Module, Patient, Provider, Room, Service
from tests.conftest import login_token


def test_readiness_requires_login(client):
    response = client.get("/api/readiness")

    assert response.status_code == 401


def test_readiness_reports_demo_guardrails(client, db, auth_setup):
    db.add_all(
        [
            Patient(first_name="Ana", last_name="Horvat"),
            Provider(full_name="Dr. Demo", active=True),
            Room(name="Soba 1", active=True),
            Module(key="core", name="Clinic Core", enabled=True),
            Service(name="Pregled", duration_minutes=30, price="50.00", active=True),
        ]
    )
    db.commit()
    token = login_token(client, "admin@test.local")

    response = client.get("/api/readiness", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["demo_mode"] is True
    assert payload["real_data_allowed"] is False
    assert payload["fiscalization_mode"] == "noop"
    assert payload["summary"]["critical"] == 0
    assert any(check["key"] == "demo_guardrail" and check["status"] == "ok" for check in payload["checks"])
    assert any(check["key"] == "fiscalization" and check["status"] == "warning" for check in payload["checks"])
    assert any(check["key"] == "patients" and check["target_path"] == "/patients" for check in payload["checks"])
    assert any(check["key"] == "services" and check["target_path"] == "/services" for check in payload["checks"])
    assert any(check["key"] == "audit" and check["target_path"] == "/audit-log" for check in payload["checks"])
    assert any(check["key"] == "human_pilot_evidence" and check["status"] == "warning" for check in payload["checks"])
    assert any(check["key"] == "fiscalization" and check["decision_impact"] == "review" for check in payload["checks"])
    assert any(check["key"] == "human_pilot_evidence" and check["decision_impact"] == "blocks_release" for check in payload["checks"])


def test_readiness_missing_core_setup_blocks_demo(client, auth_setup):
    token = login_token(client, "admin@test.local")

    response = client.get("/api/readiness", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "blocked"
    assert any(check["key"] == "providers" and check["decision_impact"] == "blocks_demo" for check in payload["checks"])
    assert any(check["key"] == "rooms" and check["decision_impact"] == "blocks_demo" for check in payload["checks"])
    assert any(check["key"] == "services" and check["decision_impact"] == "blocks_demo" for check in payload["checks"])


def test_readiness_checks_keep_operational_evidence_contract(client, db, auth_setup):
    db.add_all(
        [
            Patient(first_name="Ana", last_name="Horvat"),
            Provider(full_name="Dr. Demo", active=True),
            Room(name="Soba 1", active=True),
            Module(key="core", name="Clinic Core", enabled=True),
            Service(name="Pregled", duration_minutes=30, price="50.00", active=True),
        ]
    )
    db.commit()
    token = login_token(client, "admin@test.local")

    response = client.get("/api/readiness", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    checks = response.json()["checks"]
    allowed_impacts = {"none", "review", "blocks_demo", "blocks_release"}
    allowed_targets = {
        "/readiness",
        "/patients",
        "/appointments/new",
        "/services",
        "/modules",
        "/audit-log",
        "/inventory",
        "/invoices",
        "/api-keys",
        "/clinical-documents",
        "/clinical-documents?physician_reviewed=false",
        "/reception",
        }

    assert checks
    for check in checks:
        assert check["decision_impact"] in allowed_impacts
        assert check["target_path"] in allowed_targets
        assert check["target_label"]
        if check["status"] in {"warning", "critical"}:
            assert check["action"] or check["target_path"]


def test_readiness_does_not_block_or_warn_on_missing_episodes(client, db, auth_setup):
    db.add_all(
        [
            Patient(first_name="Ana", last_name="Horvat"),
            Provider(full_name="Dr. Demo", active=True),
            Room(name="Soba 1", active=True),
            Module(key="core", name="Clinic Core", enabled=True),
            Service(name="Pregled", duration_minutes=30, price="50.00", active=True),
        ]
    )
    db.commit()
    token = login_token(client, "admin@test.local")

    response = client.get("/api/readiness", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    episode_check = next(check for check in response.json()["checks"] if check["key"] == "clinical_episodes")
    assert episode_check["status"] == "ok"
    assert episode_check["decision_impact"] == "none"
    assert episode_check["target_path"] == "/clinical-documents"
