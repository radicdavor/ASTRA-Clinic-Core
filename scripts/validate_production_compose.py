from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
COMPOSE = ROOT / "docker-compose.prod.example.yml"

SYNTHETIC_ENV = """\
APP_ENV=production
ENVIRONMENT=production
POSTGRES_DB=astra_validation
POSTGRES_USER=astra_validation
POSTGRES_PASSWORD=synthetic-validation-password-2026
DATABASE_URL=postgresql+psycopg://astra_validation:synthetic-validation-password-2026@db:5432/astra_validation
JWT_SECRET=synthetic-validation-jwt-secret-with-at-least-48-characters
ACCESS_TOKEN_MINUTES=480
BROWSER_SESSION_MINUTES=480
SESSION_COOKIE_NAME=astra_session
CSRF_COOKIE_NAME=astra_csrf
SESSION_COOKIE_SAMESITE=lax
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
BROWSER_PUBLIC_ORIGIN=https://astra-validation.invalid
CORS_ORIGINS=https://astra-validation.invalid
CORS_ORIGIN_REGEX=
DEBUG=false
RELOAD=false
DEMO_MODE=false
DEMO_SEED_ENABLED=false
DEMO_PERSONA_SWITCHER_ENABLED=false
AUTO_CREATE_DEFAULT_ADMIN=false
REAL_DATA_ALLOWED=true
FISCALIZATION_MODE=production
OCR_PROVIDER_MODE=production
REMINDER_PROVIDER_MODE=production
AI_SUMMARY_PROVIDER_MODE=production
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
AI_DIAGNOSIS_SUGGESTIONS_ENABLED=false
AI_DIAGNOSIS_SUGGESTIONS_PRODUCTION_AUTHORIZED=false
VITE_API_BASE_URL=
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="astra-production-validation-") as directory:
        env_file = Path(directory) / ".env.production.validation"
        env_file.write_text(SYNTHETIC_ENV, encoding="utf-8")
        result = subprocess.run(
            [
                "docker",
                "compose",
                "--env-file",
                str(env_file),
                "-f",
                str(COMPOSE),
                "config",
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        config = json.loads(result.stdout)

        services = config["services"]
        backend = services["backend"]
        frontend = services["frontend"]
        database = services["db"]
        backend_env = backend["environment"]
        frontend_args = frontend["build"].get("args", {})

        require(backend_env["APP_ENV"] == "production", "Backend must use production APP_ENV.")
        require(backend_env["DEMO_MODE"] == "false", "Production demo mode must be disabled.")
        require(backend_env["DEMO_SEED_ENABLED"] == "false", "Production demo seed must be disabled.")
        require(
            backend_env["DEMO_PERSONA_SWITCHER_ENABLED"] == "false",
            "Production persona switcher must be disabled.",
        )
        require(backend_env["CORS_ORIGINS"] == backend_env["BROWSER_PUBLIC_ORIGIN"], "Same-origin contract mismatch.")
        require(not backend_env.get("CORS_ORIGIN_REGEX"), "Production CORS regex must be empty.")
        require("ports" not in backend, "Backend must not publish a development host port.")
        require(frontend_args.get("VITE_API_BASE_URL", "") == "", "Frontend API must remain same-origin.")
        require("OPENAI_API_KEY" not in frontend_args, "Server-side OpenAI key reached frontend build args.")
        require("environment" not in frontend or "OPENAI_API_KEY" not in frontend["environment"], "Server secret reached frontend.")
        require(bool(backend.get("healthcheck")), "Backend healthcheck is required.")
        require(bool(database.get("healthcheck")), "Database healthcheck is required.")
        require(bool(database.get("volumes")), "Persistent PostgreSQL storage is required.")

        sys.path.insert(0, str(BACKEND))
        from app.core.config import Settings  # noqa: PLC0415

        runtime_values = {}
        for line in SYNTHETIC_ENV.splitlines():
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            field = key.lower()
            if field in Settings.model_fields:
                runtime_values[field] = value
        Settings(**runtime_values).validate_production_safety()

    print("Production Compose contract passed with synthetic configuration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
