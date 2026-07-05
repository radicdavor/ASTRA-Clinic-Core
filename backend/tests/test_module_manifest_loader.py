import json

import pytest
from pydantic import ValidationError

from app.models.domain import InventoryItem, Module, Service, ServiceMaterialTemplate
from app.modules.manifest import ModuleManifest, load_catalog_material_templates, load_catalog_module, load_module_manifests


def write_json(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_loading_one_module_creates_module_record(db, tmp_path):
    module_dir = tmp_path / "gastro"
    module_dir.mkdir()
    write_json(module_dir / "module.json", {"name": "gastro", "display_name": "Gastro", "enabled": True})

    result = load_catalog_module(db, module_dir)

    module = db.query(Module).filter(Module.key == "gastro").one()
    assert result["modules"] == 1
    assert module.name == "Gastro"
    assert module.enabled is True


def test_loading_same_module_twice_does_not_create_duplicates(db, tmp_path):
    module_dir = tmp_path / "gastro"
    module_dir.mkdir()
    write_json(module_dir / "module.json", {"name": "gastro", "display_name": "Gastro"})

    load_catalog_module(db, module_dir)
    load_catalog_module(db, module_dir)

    assert db.query(Module).filter(Module.key == "gastro").count() == 1


def test_loading_services_creates_records_by_code(db, tmp_path):
    module_dir = tmp_path / "gastro"
    module_dir.mkdir()
    write_json(module_dir / "module.json", {"name": "gastro", "display_name": "Gastro"})
    write_json(module_dir / "services.json", [{"code": "GASTRO", "name": "Gastroskopija", "duration_minutes": 30, "price": "50"}])

    load_catalog_module(db, module_dir)

    service = db.query(Service).filter(Service.code == "GASTRO").one()
    assert service.name == "Gastroskopija"
    assert str(service.price) == "50.00"


def test_loading_services_twice_updates_without_duplication(db, tmp_path):
    module_dir = tmp_path / "gastro"
    module_dir.mkdir()
    write_json(module_dir / "module.json", {"name": "gastro", "display_name": "Gastro"})
    write_json(module_dir / "services.json", [{"code": "GASTRO", "name": "Old", "duration_minutes": 30, "price": "50"}])

    load_catalog_module(db, module_dir)
    write_json(module_dir / "services.json", [{"code": "GASTRO", "name": "New", "duration_minutes": 45, "price": "75"}])
    load_catalog_module(db, module_dir)

    service = db.query(Service).filter(Service.code == "GASTRO").one()
    assert service.name == "New"
    assert service.duration_minutes == 45
    assert db.query(Service).filter(Service.code == "GASTRO").count() == 1


def test_loading_material_templates_creates_by_service_code_and_item_sku(db, tmp_path):
    module_dir = tmp_path / "gastro"
    module_dir.mkdir()
    write_json(module_dir / "module.json", {"name": "gastro", "display_name": "Gastro"})
    write_json(module_dir / "services.json", [{"code": "GASTRO", "name": "Gastroskopija"}])
    write_json(module_dir / "material_templates.json", [{"service_code": "GASTRO", "item_sku": "BIOPSY", "default_quantity": "2", "required": True}])
    db.add(InventoryItem(sku="BIOPSY", name="Biopsy forceps"))
    db.flush()

    load_catalog_module(db, module_dir)

    template = db.query(ServiceMaterialTemplate).one()
    assert template.service.code == "GASTRO"
    assert template.item.sku == "BIOPSY"
    assert str(template.default_quantity) == "2.00"


def test_missing_inventory_item_for_material_template_is_skipped(db, tmp_path):
    module_dir = tmp_path / "gastro"
    module_dir.mkdir()
    write_json(module_dir / "services.json", [{"code": "GASTRO", "name": "Gastroskopija"}])
    write_json(module_dir / "material_templates.json", [{"service_code": "GASTRO", "item_sku": "MISSING"}])
    load_catalog_module(db, module_dir)

    assert load_catalog_material_templates(db, module_dir) == []
    assert db.query(ServiceMaterialTemplate).count() == 0


def test_invalid_module_manifest_fails_with_validation_error():
    with pytest.raises(ValidationError, match="display_name"):
        ModuleManifest.model_validate({"name": "broken"})


def test_loader_does_not_execute_arbitrary_python_code(tmp_path):
    marker = tmp_path / "executed.txt"
    write_json(
        tmp_path / "safe.json",
        {
            "name": "safe",
            "display_name": "Safe",
            "permissions": [f"__import__('pathlib').Path(r'{marker}').write_text('bad')"],
        },
    )

    manifests = load_module_manifests(tmp_path)

    assert manifests[0].name == "safe"
    assert not marker.exists()
