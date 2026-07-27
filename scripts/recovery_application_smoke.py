from __future__ import annotations

import json
import os

from fastapi.testclient import TestClient
import psycopg

from app.main import app


PASSWORD = "synthetic-membership-test"
PREFIX = "membership-migration-"


def expect(response, status: int = 200) -> None:
    if response.status_code != status:
        raise RuntimeError(
            f"unexpected_http_status:{response.request.url.path}:{response.status_code}"
        )


def main() -> int:
    database_url = os.environ["DATABASE_URL"].replace(
        "postgresql+psycopg://", "postgresql://", 1
    )
    with psycopg.connect(database_url) as connection:
        clinic_id = int(
            connection.execute(
                "SELECT id FROM clinics WHERE name=%s",
                (f"{PREFIX}clinic-a",),
            ).fetchone()[0]
        )
        episode_row = connection.execute(
            "SELECT id FROM clinical_episodes WHERE title='RECOVERY-SYNTHETIC-EPISODE'"
        ).fetchone()

    checks = 0
    with TestClient(app) as client:
        expect(client.get("/health"))
        checks += 1
        expect(client.get("/ready"))
        checks += 1

        login = client.post(
            "/auth/login",
            json={
                "email": f"{PREFIX}provider@example.invalid",
                "password": PASSWORD,
            },
        )
        expect(login)
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        clinics = client.get("/auth/me/clinics", headers=headers)
        expect(clinics)
        if clinic_id not in {item["id"] for item in clinics.json()["clinics"]}:
            raise RuntimeError("restored_membership_not_visible")
        checks += 2

        reviewer_headers = {
            "Authorization": f"Bearer {login.json()['access_token']}",
            "X-Clinic-Id": str(clinic_id),
        }
        expect(
            client.get(
                "/api/document-classification-queue", headers=reviewer_headers
            )
        )
        checks += 1
        if episode_row:
            expect(
                client.get(
                    f"/api/episodes/{int(episode_row[0])}/appointments",
                    headers=reviewer_headers,
                )
            )
            checks += 1

    print(json.dumps({"status": "passed", "checks": checks}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
