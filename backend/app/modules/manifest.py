from pathlib import Path
from decimal import Decimal
import json

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import InventoryItem, Service, ServiceMaterialTemplate


class ModuleManifest(BaseModel):
    name: str
    display_name: str
    version: str = "0.1.0"
    enabled: bool = False
    permissions: list[str] = []

    model_config = ConfigDict(extra="forbid")


def load_module_manifests(directory: Path) -> list[ModuleManifest]:
    if not directory.exists():
        return []
    manifests: list[ModuleManifest] = []
    for path in sorted(directory.glob("*.json")):
        manifests.append(ModuleManifest.model_validate_json(path.read_text(encoding="utf-8")))
    return manifests


def load_catalog_manifests(directory: Path) -> list[ModuleManifest]:
    if not directory.exists():
        return []
    return [
        ModuleManifest.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*/module.json"))
    ]


def load_catalog_services(db: Session, module_directory: Path) -> list[Service]:
    services_path = module_directory / "services.json"
    if not services_path.exists():
        return []
    services: list[Service] = []
    for data in json.loads(services_path.read_text(encoding="utf-8")):
        service = db.scalar(select(Service).where(Service.code == data.get("code"))) if data.get("code") else None
        if service is None:
            service = Service()
            db.add(service)
        service.name = data["name"]
        service.code = data.get("code")
        service.duration_minutes = int(data.get("duration_minutes", 30))
        service.price = Decimal(str(data.get("price", "0")))
        service.active = bool(data.get("active", True))
        services.append(service)
    db.flush()
    return services


def load_catalog_material_templates(db: Session, module_directory: Path) -> list[ServiceMaterialTemplate]:
    templates_path = module_directory / "material_templates.json"
    if not templates_path.exists():
        return []
    templates: list[ServiceMaterialTemplate] = []
    for data in json.loads(templates_path.read_text(encoding="utf-8")):
        service = db.scalar(select(Service).where(Service.code == data["service_code"]))
        item = db.scalar(select(InventoryItem).where(InventoryItem.sku == data["item_sku"]))
        if service is None or item is None:
            continue
        template = db.scalar(select(ServiceMaterialTemplate).where(ServiceMaterialTemplate.service_id == service.id, ServiceMaterialTemplate.inventory_item_id == item.id))
        if template is None:
            template = ServiceMaterialTemplate(service_id=service.id, inventory_item_id=item.id)
            db.add(template)
        template.default_quantity = Decimal(str(data.get("default_quantity", "1")))
        template.required = bool(data.get("required", True))
        template.variable_quantity_allowed = bool(data.get("variable_quantity_allowed", False))
        template.notes = data.get("notes")
        templates.append(template)
    db.flush()
    return templates
