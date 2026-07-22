from __future__ import annotations

import argparse
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def expect(response, status: int = 200) -> None:
    if response.status_code != status:
        raise RuntimeError(f"unexpected_http_status:{response.request.url.path}:{response.status_code}")


def expect_denied(response) -> None:
    if response.status_code not in {403, 404}:
        raise RuntimeError(f"access_not_denied:{response.request.url.path}:{response.status_code}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run security-aware smoke checks against a restored synthetic database")
    parser.add_argument("--seed-file", type=Path, required=True)
    args = parser.parse_args()
    seed = json.loads(args.seed_file.read_text(encoding="utf-8"))

    with TestClient(app) as client:
        expect(client.get("/health"))
        expect(client.get("/ready"))

        client.cookies.set("astra_session", "recovery-active-session")
        expect(client.get("/auth/session"), 401)
        client.cookies.clear()

        expect(
            client.post(
                "/auth/browser/login",
                json={"email": seed["users"]["adminA"], "password": seed["password"]},
            )
        )
        clinic_headers = {"X-Clinic-Id": str(seed["clinics"]["a"])}
        expect(client.get(f"/api/dashboard/day?selected_date={seed['date']}", headers=clinic_headers))
        expect(client.get("/api/invoices", headers=clinic_headers))

        client.cookies.clear()
        expect(
            client.post(
                "/auth/browser/login",
                json={"email": seed["users"]["physicianA"], "password": seed["password"]},
            )
        )
        expect(client.get(f"/api/patients/{seed['patients']['shared']}/clinical-record", headers=clinic_headers))
        expect(client.get(f"/api/signed-reports/{seed['clinical']['signedReport']}", headers=clinic_headers))
        expect(client.get(f"/api/clinical-documents/{seed['clinical']['signedDocument']}/source", headers=clinic_headers))
        expect_denied(client.get(f"/api/clinical-documents/{seed['clinical']['foreignDocument']}", headers=clinic_headers))

    print(json.dumps({"status": "passed", "checks": 11}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
