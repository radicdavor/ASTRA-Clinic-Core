from pathlib import Path

from pydantic import BaseModel, ConfigDict


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
