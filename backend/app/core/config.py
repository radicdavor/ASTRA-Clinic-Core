from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ASTRA Clinic Core"
    app_env: Literal["development", "production"] = "development"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://astra:astra@db:5432/astra_clinic"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_origin_regex: str | None = r"^https?://(localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})(:\d+)?$"
    demo_mode: bool = True
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

    def validate_production_safety(self) -> None:
        if self.app_env != "production":
            return
        weak_secrets = {"change-me-in-production", "change-this-local-secret", "dev", "secret"}
        if self.jwt_secret in weak_secrets or len(self.jwt_secret) < 32:
            raise RuntimeError("Production APP_ENV requires a strong JWT_SECRET with at least 32 characters.")
        if "*" in self.cors_origin_list or any("localhost" in origin or "127.0.0.1" in origin for origin in self.cors_origin_list):
            raise RuntimeError("Production APP_ENV requires explicit non-local CORS_ORIGINS.")
        if self.cors_origin_regex:
            raise RuntimeError("Production APP_ENV requires CORS_ORIGIN_REGEX to be empty and CORS_ORIGINS to list explicit domains.")
        if self.ai_diagnosis_suggestions_enabled and not self.ai_diagnosis_suggestions_production_authorized:
            raise RuntimeError("AI diagnosis suggestions require separate explicit production authorization.")
        unsafe_stub_modes = {
            "FISCALIZATION_MODE": self.fiscalization_mode in {"noop", "croatia_stub"},
            "OCR_PROVIDER_MODE": self.ocr_provider_mode == "local_demo",
            "REMINDER_PROVIDER_MODE": self.reminder_provider_mode == "local_demo",
            "AI_SUMMARY_PROVIDER_MODE": self.ai_summary_provider_mode == "local_deterministic",
        }
        configured_stubs = [name for name, unsafe in unsafe_stub_modes.items() if unsafe]
        if configured_stubs:
            raise RuntimeError(f"Production cannot start with demo/stub providers: {', '.join(configured_stubs)}.")

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
