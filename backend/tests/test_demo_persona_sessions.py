from app.core.config import Settings
from app.core.security import hash_password
from app.models.domain import AuditLog, ClinicMembership, Role, User, UserSession
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
        db.add(
            ClinicMembership(
                user_id=user.id,
                clinic_id=auth_setup["clinic"].id,
                active=True,
                created_by_user_id=auth_setup["admin"].id,
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
