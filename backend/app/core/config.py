from functools import lru_cache
from typing import Literal

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
