from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoClinicalReadinessBinding:
    template_key: str
    reason: str


EXPLICIT_BINDING_WARNING = "Template je odabran iz demo/pilot explicit service binding konfiguracije; nije produkcijsko pravilo."


DEMO_SERVICE_CODE_BINDINGS: dict[str, DemoClinicalReadinessBinding] = {
    "GASTROSCOPY": DemoClinicalReadinessBinding("gastroscopy", "Demo binding za gastroskopiju prema service codeu."),
    "GASTRO": DemoClinicalReadinessBinding("gastroscopy", "Demo binding za gastroskopiju prema service codeu."),
    "COLONOSCOPY": DemoClinicalReadinessBinding("colonoscopy", "Demo binding za kolonoskopiju prema service codeu."),
    "COLO": DemoClinicalReadinessBinding("colonoscopy", "Demo binding za kolonoskopiju prema service codeu."),
    "HPYLORI": DemoClinicalReadinessBinding("hpylori", "Demo binding za H. pylori prema service codeu."),
    "H_PYLORI": DemoClinicalReadinessBinding("hpylori", "Demo binding za H. pylori prema service codeu."),
    "FILLER": DemoClinicalReadinessBinding("aesthetic_injectable", "Demo binding za injektivne estetske tretmane."),
    "BOTOX": DemoClinicalReadinessBinding("aesthetic_injectable", "Demo binding za injektivne estetske tretmane."),
    "SKINBOOSTER": DemoClinicalReadinessBinding("aesthetic_skinbooster_pn", "Demo binding za skinbooster/PN tretmane."),
    "PN": DemoClinicalReadinessBinding("aesthetic_skinbooster_pn", "Demo binding za polinukleotidne tretmane."),
    "LASER": DemoClinicalReadinessBinding("aesthetic_energy_device", "Demo binding za energy-device tretmane."),
    "RF": DemoClinicalReadinessBinding("aesthetic_energy_device", "Demo binding za RF/energy-device tretmane."),
    "EXION": DemoClinicalReadinessBinding("aesthetic_energy_device", "Demo binding za Exion tretmane."),
}


DEMO_SERVICE_NAME_BINDINGS: dict[str, DemoClinicalReadinessBinding] = {
    "gastroskopija": DemoClinicalReadinessBinding("gastroscopy", "Demo binding za tocni naziv usluge."),
    "kolonoskopija": DemoClinicalReadinessBinding("colonoscopy", "Demo binding za tocni naziv usluge."),
    "eradikacija h. pylori": DemoClinicalReadinessBinding("hpylori", "Demo binding za tocni naziv usluge."),
    "dermalni filler": DemoClinicalReadinessBinding("aesthetic_injectable", "Demo binding za tocni naziv usluge."),
    "pn / skinbooster": DemoClinicalReadinessBinding("aesthetic_skinbooster_pn", "Demo binding za tocni naziv usluge."),
    "energy device / rf / exion": DemoClinicalReadinessBinding("aesthetic_energy_device", "Demo binding za tocni naziv usluge."),
}


def normalize_service_code(service_code: str | None) -> str:
    return (service_code or "").strip().upper()


def find_demo_explicit_binding(
    *,
    service_code: str | None,
    normalized_service_name: str,
) -> DemoClinicalReadinessBinding | None:
    code_binding = DEMO_SERVICE_CODE_BINDINGS.get(normalize_service_code(service_code))
    if code_binding:
        return code_binding
    return DEMO_SERVICE_NAME_BINDINGS.get(normalized_service_name)
