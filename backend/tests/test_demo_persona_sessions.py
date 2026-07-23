from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.core.security import hash_password
from app.models.domain import AuditLog, Clinic, ClinicMembership, Provider, Role, User, UserSession
from app.services.seed import ROLE_PERMISSIONS, ROLE_PROFESSIONAL_CATEGORIES


PERSONA_EMAILS = {
    "admin": "demo.admin@astra.local",
    "receptionist": "demo.reception@astra.local",
    "nurse": "demo.nurse@astra.local",
    "physician_1": "demo.physician@astra.local",
    "physician_2": "demo.physician2@astra.local",
}


def enable_switcher(monkeypatch):
    settings = Settings(
        app_env="test",
        demo_mode=True,
        real_data_allowed=False,
        demo_persona_switcher_enabled=True,
    )
    monkeypatch.setattr("app.api.routes.auth.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.sessions.get_settings", lambda: settings)
    return settings


def seed_personas(db, auth_setup):
    permission_by_name = {permission.name: permission for permission in auth_setup["admin"].role.permissions}
    auth_setup["admin"].email = PERSONA_EMAILS["admin"]
    auth_setup["admin"].role.name = "demo_admin"
    auth_setup["admin"].role.professional_category = "administrative"
    clinic_a = auth_setup["clinic"]
    clinic_b = Clinic(
        name="Test Clinic B",
        institution_key=clinic_a.institution_key,
        institution=clinic_a.institution,
    )
    db.add(clinic_b)
    db.flush()
    db.add(
        ClinicMembership(
            user_id=auth_setup["admin"].id,
            clinic_id=clinic_b.id,
            active=True,
            created_by_user_id=auth_setup["admin"].id,
        )
    )
    users = {"admin": auth_setup["admin"]}
    roles = {}
    for key, role_name in [
        ("receptionist", "receptionist"),
        ("nurse", "nurse"),
        ("physician_1", "physician"),
        ("physician_2", "physician"),
    ]:
        role = roles.get(role_name)
        if role is None:
            role = Role(
                name=f"demo_{role_name}",
                description=role_name,
                professional_category=ROLE_PROFESSIONAL_CATEGORIES.get(role_name, "administrative"),
                permissions=[
                    permission_by_name[name]
                    for name in ROLE_PERMISSIONS[role_name]
                    if name in permission_by_name
                ],
            )
            roles[role_name] = role
            db.add(role)
        user = User(
            email=PERSONA_EMAILS[key],
            full_name=key,
            password_hash=hash_password("unused"),
            role=role,
            active=True,
        )
        db.add(user)
        db.flush()
        clinic = clinic_b if key == "physician_2" else clinic_a
        db.add(
            ClinicMembership(
                user_id=user.id,
                clinic_id=clinic.id,
                active=True,
                created_by_user_id=auth_setup["admin"].id,
            )
        )
        if key.startswith("physician_"):
            db.add(
                Provider(
                    full_name=key,
                    email=user.email,
                    specialty="gastroenterology" if key == "physician_1" else "aesthetic_medicine",
                    staff_role="physician",
                    clinic_id=clinic.id,
                )
            )
        users[key] = user
    db.flush()
    return users


def login_controller(client):
    response = client.post(
        "/auth/browser/login",
        json={"email": PERSONA_EMAILS["admin"], "password": "secret"},
    )
    assert response.status_code == 200
    return response.json()["csrf_token"]


def test_demo_persona_switch_uses_actual_user_session_and_is_audited(client, db, auth_setup, monkeypatch):
    enable_switcher(monkeypatch)
    users = seed_personas(db, auth_setup)
    csrf = login_controller(client)

    response = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": csrf},
        json={"persona_key": "physician_2"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == users["physician_2"].id
    assert response.json()["user"]["role"] == "demo_physician"
    assert response.json()["csrf_token"] != csrf
    assert client.get("/auth/session").json()["user"]["id"] == users["physician_2"].id
    event = db.query(AuditLog).filter(AuditLog.action == "demo_persona_switched").one()
    assert event.actor_user_id == users["admin"].id
    assert event.after_json == {"persona_key": "physician_2", "effective_user_id": users["physician_2"].id}


def test_demo_controller_can_switch_again_and_logout_revokes_both_sessions(client, db, auth_setup, monkeypatch):
    enable_switcher(monkeypatch)
    seed_personas(db, auth_setup)
    csrf = login_controller(client)
    first = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": csrf},
        json={"persona_key": "nurse"},
    )
    second = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": first.json()["csrf_token"]},
        json={"persona_key": "receptionist"},
    )
    assert second.status_code == 200

    logout = client.post("/auth/browser/logout", headers={"X-CSRF-Token": second.json()["csrf_token"]})

    assert logout.status_code == 200
    assert db.query(UserSession).filter(UserSession.revoked_at.is_(None)).count() == 0


def test_all_five_personas_use_seeded_roles_memberships_and_provider_assignments(client, db, auth_setup, monkeypatch):
    enable_switcher(monkeypatch)
    users = seed_personas(db, auth_setup)
    csrf = login_controller(client)

    expected = {
        "admin": ("demo_admin", "administrative", {"Test Clinic", "Test Clinic B"}),
        "receptionist": ("demo_receptionist", "administrative", {"Test Clinic"}),
        "nurse": ("demo_nurse", "medical_staff", {"Test Clinic"}),
        "physician_1": ("demo_physician", "medical_staff", {"Test Clinic"}),
        "physician_2": ("demo_physician", "medical_staff", {"Test Clinic B"}),
    }
    for persona_key, (role_name, category, clinic_names) in expected.items():
        response = client.post(
            "/auth/demo/persona-session",
            headers={"X-CSRF-Token": csrf},
            json={"persona_key": persona_key},
        )
        assert response.status_code == 200
        csrf = response.json()["csrf_token"]
        assert response.json()["user"]["id"] == users[persona_key].id
        assert response.json()["user"]["role"] == role_name
        assert users[persona_key].role.professional_category == category
        memberships = client.get("/auth/me/clinics")
        assert memberships.status_code == 200
        assert {clinic["name"] for clinic in memberships.json()["clinics"]} == clinic_names

    providers = {provider.email: provider for provider in db.query(Provider).all()}
    assert providers[PERSONA_EMAILS["physician_1"]].clinic.name == "Test Clinic"
    assert providers[PERSONA_EMAILS["physician_2"]].clinic.name == "Test Clinic B"
    assert "clinical.documents.read_institution" not in {
        permission.name for permission in users["receptionist"].role.permissions
    }
    assert "clinical.documents.read_institution" in {
        permission.name for permission in users["nurse"].role.permissions
    }
    assert "admin.manage_users" in {
        permission.name for permission in users["admin"].role.permissions
    }


def test_switch_revokes_previous_persona_and_rejects_old_csrf(client, db, auth_setup, monkeypatch):
    enable_switcher(monkeypatch)
    seed_personas(db, auth_setup)
    controller_csrf = login_controller(client)
    first = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": controller_csrf},
        json={"persona_key": "physician_1"},
    )
    first_csrf = first.json()["csrf_token"]
    first_token = client.cookies.get("astra_session")

    second = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": first_csrf},
        json={"persona_key": "physician_2"},
    )
    assert second.status_code == 200
    assert db.query(UserSession).filter(
        UserSession.user_id == db.query(User).filter(User.email == PERSONA_EMAILS["physician_1"]).one().id,
        UserSession.revoked_at.is_not(None),
    ).count() == 1

    old_csrf = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": first_csrf},
        json={"persona_key": "nurse"},
    )
    assert old_csrf.status_code == 403

    client.cookies.set("astra_session", first_token)
    client.cookies.set("astra_csrf", first_csrf)
    assert client.get("/auth/session").status_code == 401


def test_demo_switch_audit_never_contains_session_or_csrf_tokens(client, db, auth_setup, monkeypatch):
    enable_switcher(monkeypatch)
    seed_personas(db, auth_setup)
    controller_csrf = login_controller(client)
    response = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": controller_csrf},
        json={"persona_key": "nurse"},
    )
    event = db.query(AuditLog).filter(AuditLog.action == "demo_persona_switched").one()
    serialized = str(event.before_json) + str(event.after_json) + str(event.summary)

    assert controller_csrf not in serialized
    assert response.json()["csrf_token"] not in serialized
    assert client.cookies.get("astra_session") not in serialized


def test_demo_persona_switch_fails_closed_without_flag(client, auth_setup):
    csrf = client.post(
        "/auth/browser/login",
        json={"email": "admin@test.local", "password": "secret"},
    ).json()["csrf_token"]

    response = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": csrf},
        json={"persona_key": "admin"},
    )

    assert response.status_code == 404


def test_demo_persona_switch_fails_closed_in_real_data_mode(client, auth_setup, monkeypatch):
    settings = Settings(
        app_env="test",
        demo_mode=True,
        real_data_allowed=True,
        demo_persona_switcher_enabled=True,
    )
    monkeypatch.setattr("app.api.routes.auth.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.sessions.get_settings", lambda: settings)
    csrf = client.post(
        "/auth/browser/login",
        json={"email": "admin@test.local", "password": "secret"},
    ).json()["csrf_token"]

    response = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": csrf},
        json={"persona_key": "admin"},
    )

    assert response.status_code == 404


def test_expired_demo_controller_cannot_switch_persona(client, db, auth_setup, monkeypatch):
    enable_switcher(monkeypatch)
    seed_personas(db, auth_setup)
    csrf = login_controller(client)
    session = db.query(UserSession).filter(
        UserSession.user_id == auth_setup["admin"].id,
        UserSession.revoked_at.is_(None),
    ).one()
    session.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    response = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": csrf},
        json={"persona_key": "nurse"},
    )

    assert response.status_code == 403


def test_demo_persona_switch_rejects_non_controller_and_unknown_key(client, db, auth_setup, monkeypatch):
    enable_switcher(monkeypatch)
    seed_personas(db, auth_setup)
    limited_login = client.post(
        "/auth/browser/login",
        json={"email": "limited@test.local", "password": "secret"},
    )
    denied = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": limited_login.json()["csrf_token"]},
        json={"persona_key": "nurse"},
    )
    unknown = client.post(
        "/auth/demo/persona-session",
        headers={"X-CSRF-Token": limited_login.json()["csrf_token"]},
        json={"persona_key": "arbitrary-user"},
    )

    assert denied.status_code == 403
    assert unknown.status_code == 422
