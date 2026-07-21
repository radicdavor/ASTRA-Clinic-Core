from datetime import UTC, datetime, timedelta

from app.models.domain import UserSession
from app.services.sessions import cleanup_expired_sessions, create_user_session
from tests.conftest import login_token


def test_browser_login_sets_httponly_cookie_without_returning_access_token(client, db, auth_setup):
    response = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})

    assert response.status_code == 200
    body = response.json()
    assert "access_token" not in body
    assert body["user"]["email"] == "admin@test.local"
    assert body["csrf_token"]
    assert "astra_session=" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    stored = db.query(UserSession).one()
    assert stored.token_hash
    assert stored.token_hash not in response.headers["set-cookie"]
    assert stored.token_hash != body["csrf_token"]


def test_browser_session_authenticates_current_session_and_current_permissions(client, db, auth_setup):
    login = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})
    assert login.status_code == 200

    response = client.get("/auth/session")

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"


def test_logout_revokes_browser_session_and_cookie_no_longer_authenticates(client, db, auth_setup):
    login = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})
    csrf = login.json()["csrf_token"]
    assert db.query(UserSession).one().revoked_at is None

    logout = client.post("/auth/browser/logout", headers={"X-CSRF-Token": csrf})

    assert logout.status_code == 200
    assert logout.json()["logged_out"] is True
    assert "Max-Age=0" in logout.headers["set-cookie"]
    assert db.query(UserSession).one().revoked_at is not None
    assert client.get("/auth/session").status_code == 401


def test_logout_is_idempotent_without_session_cookie(client, auth_setup):
    response = client.post("/auth/browser/logout")

    assert response.status_code == 200
    assert response.json()["logged_out"] is True


def test_csrf_required_for_cookie_authenticated_mutation(client, auth_setup):
    login = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})
    assert login.status_code == 200

    response = client.post("/api/patients", json={"first_name": "Csrf", "last_name": "Blocked"})

    assert response.status_code == 403
    assert "CSRF" in response.text


def test_csrf_rejects_wrong_token_and_keeps_cors_visible(client, auth_setup):
    login = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})
    assert login.status_code == 200

    response = client.post(
        "/api/patients",
        headers={"Origin": "http://localhost:5173", "X-CSRF-Token": "wrong-token"},
        json={"first_name": "Csrf", "last_name": "Wrong"},
    )

    assert response.status_code == 403
    assert "CSRF" in response.text
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_csrf_rejects_disallowed_browser_origin(client, auth_setup):
    login = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})
    csrf = login.json()["csrf_token"]

    response = client.post(
        "/api/patients",
        headers={"Origin": "https://evil.example", "X-CSRF-Token": csrf},
        json={"first_name": "Origin", "last_name": "Blocked"},
    )

    assert response.status_code == 403
    assert "origin" in response.text.lower()


def test_csrf_allows_cookie_authenticated_mutation_with_matching_token(client, auth_setup):
    login = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})
    csrf = login.json()["csrf_token"]

    response = client.post("/api/patients", headers={"X-CSRF-Token": csrf}, json={"first_name": "Csrf", "last_name": "Allowed"})

    assert response.status_code == 200


def test_cors_preflight_allows_csrf_and_clinic_headers(client):
    response = client.options(
        "/api/patients",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-token,x-clinic-id",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "x-csrf-token" in response.headers["access-control-allow-headers"].lower()


def test_security_headers_are_present(client):
    response = client.get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "same-origin"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert "microphone=()" in response.headers["Permissions-Policy"]


def test_bearer_auth_remains_supported_for_non_browser_clients(client, auth_setup):
    token = login_token(client, "admin@test.local")

    response = client.get("/api/inventory/items", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_conflicting_cookie_and_bearer_credentials_are_rejected(client, auth_setup):
    cookie_login = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})
    token = login_token(client, "admin@test.local")

    response = client.get("/api/inventory/items", headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": cookie_login.json()["csrf_token"]})

    assert response.status_code == 401


def test_expired_or_disabled_user_session_is_rejected(client, db, auth_setup):
    login = client.post("/auth/browser/login", json={"email": "admin@test.local", "password": "secret"})
    session = db.query(UserSession).one()
    session.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.flush()

    assert client.get("/auth/session").status_code == 401

    session.expires_at = datetime.now(UTC) + timedelta(minutes=10)
    auth_setup["admin"].active = False
    db.flush()
    assert client.get("/auth/session").status_code == 401


def test_cleanup_expired_sessions_removes_only_revoked_expired_rows(client, db, auth_setup):
    create_user_session(db, auth_setup["admin"])
    create_user_session(db, auth_setup["admin"])
    sessions = db.query(UserSession).order_by(UserSession.id).all()
    sessions[0].revoked_at = datetime.now(UTC) - timedelta(minutes=5)
    sessions[0].expires_at = datetime.now(UTC) - timedelta(minutes=1)
    sessions[1].revoked_at = datetime.now(UTC) - timedelta(minutes=5)
    sessions[1].expires_at = datetime.now(UTC) + timedelta(minutes=10)
    db.flush()

    assert cleanup_expired_sessions(db) == 1

    remaining = db.query(UserSession).all()
    assert len(remaining) == 1
    assert remaining[0].expires_at > datetime.now(UTC)
