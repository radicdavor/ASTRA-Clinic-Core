from pathlib import Path
import json

import pytest
from pydantic import ValidationError

from app.core.config import Settings

from app.models.domain import InventoryItem, Module, Service, ServiceMaterialTemplate
from app.modules.manifest import (
    ModuleManifest,
    import_module_manifest,
    load_catalog_manifests,
    load_catalog_material_templates,
    load_catalog_module,
    load_catalog_services,
    load_module_manifests,
)


def test_production_rejects_default_jwt_secret():
    settings = Settings(app_env="production", jwt_secret="change-me-in-production", cors_origins="https://clinic.example.com")

    with pytest.raises(RuntimeError):
        settings.validate_production_safety()


def production_settings(**overrides):
    values = {
        "app_env": "production",
        "jwt_secret": "s" * 48,
        "database_url": "postgresql+psycopg://astra:strong-production-password@example-db:5432/astra_clinic",
        "cors_origins": "https://clinic.example.com",
        "cors_origin_regex": None,
        "demo_mode": False,
        "demo_seed_enabled": False,
        "auto_create_default_admin": False,
        "fiscalization_mode": "production",
        "ocr_provider_mode": "production",
        "reminder_provider_mode": "production",
        "ai_summary_provider_mode": "production",
    }
    values.update(overrides)
    return Settings(**values)


def test_valid_production_configuration_passes():
    production_settings().validate_production_safety()


def test_production_requires_secure_browser_session_cookies():
    settings = production_settings(session_cookie_secure=False)

    with pytest.raises(RuntimeError, match="Secure"):
        settings.validate_production_safety()


def test_samesite_none_requires_secure_cookies():
    settings = production_settings(session_cookie_samesite="none", csrf_cookie_secure=False)

    with pytest.raises(RuntimeError, match="SameSite=None"):
        settings.validate_production_safety()


def test_production_rejects_local_cors():
    settings = production_settings(cors_origins="http://localhost:5173")

    with pytest.raises(RuntimeError, match="localhost"):
        settings.validate_production_safety()


@pytest.mark.parametrize("secret", ["", "secret", "change-this-local-secret", "x" * 12])
def test_production_rejects_missing_default_or_short_jwt_secret(secret):
    settings = production_settings(jwt_secret=secret)

    with pytest.raises(RuntimeError, match="JWT secret"):
        settings.validate_production_safety()


@pytest.mark.parametrize("database_url", [
    "postgresql+psycopg://astra@db:5432/astra_clinic",
    "postgresql+psycopg://astra:astra@db:5432/astra_clinic",
    "postgresql+psycopg://astra:short@db:5432/astra_clinic",
])
def test_production_rejects_missing_default_or_short_database_password(database_url):
    settings = production_settings(database_url=database_url)

    with pytest.raises(RuntimeError, match="Database password"):
        settings.validate_production_safety()


def test_production_rejects_wildcard_cors_with_credentials():
    settings = production_settings(cors_origins="*")

    with pytest.raises(RuntimeError, match="Wildcard CORS"):
        settings.validate_production_safety()


@pytest.mark.parametrize("field", ["debug", "reload", "demo_mode", "demo_seed_enabled", "auto_create_default_admin"])
def test_production_rejects_unsafe_runtime_switches(field):
    settings = production_settings(**{field: True})

    with pytest.raises(RuntimeError):
        settings.validate_production_safety()


def test_production_rejects_demo_and_stub_providers():
    settings = production_settings(
        fiscalization_mode="noop",
        ocr_provider_mode="local_demo",
        reminder_provider_mode="local_demo",
        ai_summary_provider_mode="local_deterministic",
    )

    with pytest.raises(RuntimeError, match="demo/stub providers"):
        settings.validate_production_safety()


def test_development_and_test_environments_accept_explicit_development_defaults():
    Settings(app_env="development", jwt_secret="change-this-local-secret").validate_production_safety()
    Settings(app_env="test", jwt_secret="change-this-local-secret").validate_production_safety()


def test_production_error_messages_do_not_leak_secret_values():
    secret = "super-secret-but-still-short"
    database_password = "also-secret"
    settings = production_settings(
        jwt_secret=secret,
        database_url=f"postgresql+psycopg://astra:{database_password}@db:5432/astra_clinic",
    )

    with pytest.raises(RuntimeError) as exc:
        settings.validate_production_safety()

    message = str(exc.value)
    assert secret not in message
    assert database_password not in message


def test_production_compose_example_uses_placeholders_not_demo_secrets():
    compose = (Path(__file__).resolve().parents[2] / "docker-compose.prod.example.yml").read_text(encoding="utf-8")

    assert "APP_ENV=production" in compose
    assert "change-this-local-secret" not in compose
    assert "change-me-in-production" not in compose
    assert "astra:astra" not in compose
    assert "DEMO_MODE=false" in compose


@pytest.mark.xfail(strict=True, reason="PR #3 P1: documented production frontend and API origins are cross-site")
def test_production_example_uses_one_same_origin_browser_auth_contract():
    env_text = (Path(__file__).resolve().parents[2] / ".env.production.example").read_text(encoding="utf-8")

    assert "VITE_API_BASE_URL=/api" in env_text
    assert "CORS_ORIGINS=https://conceptnura.com" in env_text
    assert "VITE_API_BASE_URL=https://poliklinikanura.eu" not in env_text


def test_openapi_does_not_publish_sensitive_hash_fields(client):
    schema = client.get("/openapi.json").json()
    serialized = str(schema)

    assert "password_hash" not in serialized
    assert "key_hash" not in serialized
    assert "ErrorResponse" in serialized


def test_module_manifest_forbids_unknown_fields():
    with pytest.raises(ValidationError):
        ModuleManifest.model_validate({"name": "x", "display_name": "X", "unexpected": True})


def test_module_manifest_loader_returns_empty_for_missing_directory(tmp_path):
    assert load_module_manifests(tmp_path / "missing") == []


def test_module_manifest_loader_reads_json_without_code_execution(tmp_path):
    marker = tmp_path / "executed.txt"
    (tmp_path / "safe.json").write_text(
        json.dumps({
            "name": "safe_module",
            "display_name": "Safe module",
            "version": "1.0.0",
            "enabled": True,
            "permissions": [f"__import__('pathlib').Path(r'{marker}').write_text('bad')"],
        }),
        encoding="utf-8",
    )

    manifests = load_module_manifests(tmp_path)

    assert manifests[0].name == "safe_module"
    assert not marker.exists()


def test_catalog_manifest_loader_reads_data_only_modules():
    catalog_dir = Path(__file__).resolve().parents[1] / "app" / "modules" / "catalog"

    manifests = load_catalog_manifests(catalog_dir)

    names = {manifest.name for manifest in manifests}
    assert {"gastroenterology", "endoscopy", "dermatology_aesthetics"}.issubset(names)


def test_import_module_manifest_is_idempotent_and_updates_metadata(db, tmp_path):
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    manifest_path = module_dir / "module.json"
    manifest_path.write_text(json.dumps({"name": "pilot", "display_name": "Pilot", "version": "1.0.0", "enabled": True}), encoding="utf-8")

    first = import_module_manifest(db, module_dir)
    manifest_path.write_text(json.dumps({"name": "pilot", "display_name": "Pilot updated", "version": "1.1.0", "enabled": False}), encoding="utf-8")
    second = import_module_manifest(db, module_dir)

    assert first.id == second.id
    assert db.query(Module).filter(Module.key == "pilot").count() == 1
    assert second.name == "Pilot updated"
    assert second.enabled is False


def test_catalog_loader_imports_services_and_templates_idempotently(db):
    catalog_dir = Path(__file__).resolve().parents[1] / "app" / "modules" / "catalog" / "gastroenterology"
    db.add_all([
        InventoryItem(sku="BIOPSY-FORCEPS", name="Biopsy forceps"),
        InventoryItem(sku="SEDATION-MED", name="Sedation medication"),
    ])
    db.flush()

    load_catalog_services(db, catalog_dir)
    load_catalog_material_templates(db, catalog_dir)
    load_catalog_services(db, catalog_dir)
    load_catalog_material_templates(db, catalog_dir)

    assert db.query(Service).filter(Service.code.in_(["GASTRO", "COLONO"])).count() == 2
    assert db.query(ServiceMaterialTemplate).count() == 2


def test_catalog_loader_updates_services_by_code(db, tmp_path):
    module_dir = tmp_path / "pilot"
    module_dir.mkdir()
    (module_dir / "module.json").write_text(json.dumps({"name": "pilot", "display_name": "Pilot"}), encoding="utf-8")
    services_path = module_dir / "services.json"
    services_path.write_text(json.dumps([{"code": "PILOT", "name": "Pilot old", "duration_minutes": 20, "price": "10"}]), encoding="utf-8")

    load_catalog_module(db, module_dir)
    services_path.write_text(json.dumps([{"code": "PILOT", "name": "Pilot new", "duration_minutes": 45, "price": "25"}]), encoding="utf-8")
    load_catalog_module(db, module_dir)

    service = db.query(Service).filter(Service.code == "PILOT").one()
    assert service.name == "Pilot new"
    assert service.duration_minutes == 45
    assert str(service.price) == "25.00"
    assert db.query(Service).filter(Service.code == "PILOT").count() == 1


def test_catalog_material_loader_skips_missing_dependencies(db, tmp_path):
    module_dir = tmp_path / "pilot"
    module_dir.mkdir()
    (module_dir / "material_templates.json").write_text(
        json.dumps([{"service_code": "MISSING", "item_sku": "MISSING", "default_quantity": "1"}]),
        encoding="utf-8",
    )

    assert load_catalog_material_templates(db, module_dir) == []
