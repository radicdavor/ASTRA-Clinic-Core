from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


FORBIDDEN_DEVELOPMENT_SECRET_VALUES = {
    "",
    "change-me",
    "change-me-in-production",
    "change-this-local-secret",
    "dev",
    "dev-secret",
    "secret",
    "astra",
}


class Settings(BaseSettings):
    app_name: str = "ASTRA Clinic Core"
    app_env: Literal["development", "test", "production"] = "development"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://astra:astra@db:5432/astra_clinic"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    browser_session_minutes: int = 480
    session_cookie_name: str = "astra_session"
    csrf_cookie_name: str = "astra_csrf"
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    session_cookie_secure: bool | None = None
    csrf_cookie_secure: bool | None = None
    browser_public_origin: str = ""
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_origin_regex: str | None = r"^https?://(localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})(:\d+)?$"
    debug: bool = False
    reload: bool = False
    demo_mode: bool = True
    demo_seed_enabled: bool = False
    demo_persona_switcher_enabled: bool = False
    demo_controller_cookie_name: str = "astra_demo_controller"
    auto_create_default_admin: bool = False
    real_data_allowed: bool = False
    fiscalization_mode: str = "noop"
    ocr_provider_mode: str = "local_demo"
    reminder_provider_mode: str = "local_demo"
    ai_summary_provider_mode: str = "local_deterministic"
    document_storage_path: str = "/app/data/documents"
    document_max_upload_bytes: int = 15 * 1024 * 1024
    schema_readiness_check_on_startup: bool = False
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4.1-mini"
    ai_diagnosis_suggestions_enabled: bool = False
    ai_diagnosis_suggestions_production_authorized: bool = False
    clinical_activity_forms_required: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def production_safety_errors(self) -> list[str]:
        if self.app_env != "production":
            return []
        errors: list[str] = []
        if self.jwt_secret in FORBIDDEN_DEVELOPMENT_SECRET_VALUES or len(self.jwt_secret) < 32:
            errors.append("JWT secret is missing or uses a forbidden development value.")
        if self.session_cookie_secure is False or self.csrf_cookie_secure is False:
            errors.append("Production browser session and CSRF cookies must be Secure.")
        if self.session_cookie_samesite == "none" and (self.session_cookie_secure is False or self.csrf_cookie_secure is False):
            errors.append("SameSite=None requires Secure cookies.")
        try:
            database_url = make_url(self.database_url)
            database_password = database_url.password or ""
        except Exception:
            database_password = ""
        if database_password in FORBIDDEN_DEVELOPMENT_SECRET_VALUES or len(database_password) < 12:
            errors.append("Database password is missing or uses a forbidden development value.")
        origins = self.cors_origin_list
        public_origin = self.browser_public_origin.rstrip("/")
        if not public_origin or not public_origin.startswith("https://"):
            errors.append("Production BROWSER_PUBLIC_ORIGIN must be one explicit HTTPS origin.")
        elif origins != [public_origin]:
            errors.append("Production CORS_ORIGINS must equal the canonical BROWSER_PUBLIC_ORIGIN.")
        if not origins:
            errors.append("Production CORS_ORIGINS must list explicit origins.")
        if "*" in origins:
            errors.append("Wildcard CORS origin is forbidden when credentials are enabled.")
        if any("localhost" in origin or "127.0.0.1" in origin for origin in origins):
            errors.append("Production CORS_ORIGINS must not use localhost origins.")
        if self.cors_origin_regex:
            errors.append("Production CORS_ORIGIN_REGEX must be empty; use explicit CORS_ORIGINS.")
        if self.debug:
            errors.append("Production DEBUG must be false.")
        if self.reload:
            errors.append("Production RELOAD must be false.")
        if self.demo_mode:
            errors.append("Production DEMO_MODE must be false.")
        if self.demo_seed_enabled:
            errors.append("Production DEMO_SEED_ENABLED must be false.")
        if self.demo_persona_switcher_enabled:
            errors.append("Production DEMO_PERSONA_SWITCHER_ENABLED must be false.")
        if self.auto_create_default_admin:
            errors.append("Production AUTO_CREATE_DEFAULT_ADMIN must be false.")
        if self.ai_diagnosis_suggestions_enabled and not self.ai_diagnosis_suggestions_production_authorized:
            errors.append("AI diagnosis suggestions require separate explicit production authorization.")
        unsafe_stub_modes = {
            "FISCALIZATION_MODE": self.fiscalization_mode in {"noop", "croatia_stub"},
            "OCR_PROVIDER_MODE": self.ocr_provider_mode == "local_demo",
            "REMINDER_PROVIDER_MODE": self.reminder_provider_mode == "local_demo",
            "AI_SUMMARY_PROVIDER_MODE": self.ai_summary_provider_mode == "local_deterministic",
        }
        configured_stubs = [name for name, unsafe in unsafe_stub_modes.items() if unsafe]
        if configured_stubs:
            errors.append(f"Production cannot start with demo/stub providers: {', '.join(configured_stubs)}.")
        return errors

    @property
    def effective_session_cookie_secure(self) -> bool:
        return self.session_cookie_secure if self.session_cookie_secure is not None else self.app_env == "production"

    @property
    def effective_csrf_cookie_secure(self) -> bool:
        return self.csrf_cookie_secure if self.csrf_cookie_secure is not None else self.app_env == "production"

    def validate_production_safety(self) -> None:
        errors = self.production_safety_errors()
        if errors:
            raise RuntimeError("Invalid production configuration: " + " ".join(errors))

    @property
    def public_warnings(self) -> list[str]:
        warnings: list[str] = []
        if self.demo_mode:
            warnings.append("Demo mode is enabled. Do not enter real patient data.")
        if not self.real_data_allowed:
            warnings.append("Real patient data is not allowed in this environment.")
        if self.app_env == "production" and self.demo_mode:
            warnings.append("Production environment is still running with DEMO_MODE=true.")
        return warnings

    @property
    def demo_persona_switcher_available(self) -> bool:
        return (
            self.app_env != "production"
            and self.demo_mode
            and not self.real_data_allowed
            and self.demo_persona_switcher_enabled
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
