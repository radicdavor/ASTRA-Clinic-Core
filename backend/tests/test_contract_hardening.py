import pytest
from pydantic import ValidationError

from app.core.config import Settings
from pathlib import Path

from app.modules.manifest import ModuleManifest, load_catalog_manifests


def test_production_rejects_default_jwt_secret():
    settings = Settings(app_env="production", jwt_secret="change-me-in-production", cors_origins="https://clinic.example.com")

    with pytest.raises(RuntimeError):
        settings.validate_production_safety()


def test_production_rejects_local_cors():
    settings = Settings(app_env="production", jwt_secret="x" * 40, cors_origins="http://localhost:5173")

    with pytest.raises(RuntimeError):
        settings.validate_production_safety()


def test_openapi_does_not_publish_sensitive_hash_fields(client):
    schema = client.get("/openapi.json").json()
    serialized = str(schema)

    assert "password_hash" not in serialized
    assert "key_hash" not in serialized
    assert "ErrorResponse" in serialized


def test_module_manifest_forbids_unknown_fields():
    with pytest.raises(ValidationError):
        ModuleManifest.model_validate({"name": "x", "display_name": "X", "unexpected": True})


def test_catalog_manifest_loader_reads_data_only_modules():
    catalog_dir = Path(__file__).resolve().parents[1] / "app" / "modules" / "catalog"

    manifests = load_catalog_manifests(catalog_dir)

    names = {manifest.name for manifest in manifests}
    assert {"gastroenterology", "endoscopy", "dermatology_aesthetics"}.issubset(names)
