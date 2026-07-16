import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.journey_encounter import DiagnosisSuggestionRequest, DiagnosisSuggestionsOut


class DiagnosisSuggestionUnavailable(RuntimeError):
    pass


def get_icd10_catalog() -> dict[str, str] | None:
    """Load a repository-controlled canonical catalog when one is authorized.

    The repository currently contains no canonical WHO ICD-10 catalog. We do
    not download or invent one; absence deliberately keeps the capability off.
    """
    path = Path(__file__).resolve().parents[1] / "data" / "icd10_catalog.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {normalize_icd_code(code): str(label) for code, label in payload.items()}


def normalize_icd_code(value: str) -> str:
    return value.strip().upper().replace(" ", "")


def diagnosis_suggestions_capability(settings: Settings | None = None) -> dict[str, object]:
    settings = settings or get_settings()
    catalog_available = get_icd10_catalog() is not None
    production_allowed = settings.app_env != "production" or settings.ai_diagnosis_suggestions_production_authorized
    available = bool(
        settings.ai_diagnosis_suggestions_enabled
        and settings.openai_api_key
        and catalog_available
        and production_allowed
    )
    reason = None
    if not settings.ai_diagnosis_suggestions_enabled:
        reason = "AI prijedlozi dijagnoza isključeni su u ovom okruženju."
    elif not catalog_available:
        reason = "Kanonski WHO ICD-10 katalog nije dostupan; AI prijedlozi ostaju blokirani."
    elif not settings.openai_api_key:
        reason = "AI provider nije konfiguriran."
    elif not production_allowed:
        reason = "AI prijedlozi nemaju zasebno produkcijsko odobrenje."
    return {"enabled": available, "configured": settings.ai_diagnosis_suggestions_enabled, "catalog_available": catalog_available, "reason": reason}


def ensure_diagnosis_suggestions_enabled() -> dict[str, str]:
    settings = get_settings()
    capability = diagnosis_suggestions_capability(settings)
    if not capability["enabled"]:
        raise DiagnosisSuggestionUnavailable(str(capability["reason"]))
    return get_icd10_catalog() or {}


def build_openai_request(payload: DiagnosisSuggestionRequest, settings: Settings) -> dict:
    clinical_text = "\n".join(
        f"{label}: {value.strip()}"
        for label, value in (
            ("Anamneza", payload.anamnesis),
            ("Status", payload.examination),
            ("Doneseni nalazi", payload.patient_findings),
            ("Mišljenje liječnika", payload.opinion),
        )
        if value and value.strip()
    )
    if not clinical_text:
        raise ValueError("Prije AI prijedloga upišite kliničke podatke.")
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "diagnoses": {
                "type": "array",
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"code": {"type": "string"}, "title": {"type": "string"}},
                    "required": ["code", "title"],
                },
            }
        },
        "required": ["diagnoses"],
    }
    return {
        "model": settings.openai_model,
        "store": False,
        "max_output_tokens": 500,
        "instructions": (
            "Ti si medicinski pisani asistent liječniku u Hrvatskoj. Na temelju isključivo dostavljenog teksta "
            "predloži najviše pet mogućih dijagnoza s WHO ICD-10 šiframa. Ne donosi konačnu dijagnozu i ne dodaj "
            "podatke kojih nema. Ako podaci nisu dovoljni, vrati prazan niz."
        ),
        "input": clinical_text,
        "text": {"format": {"type": "json_schema", "name": "icd10_suggestions", "strict": True, "schema": schema}},
    }


def suggest_icd10_diagnoses(payload: DiagnosisSuggestionRequest) -> DiagnosisSuggestionsOut:
    settings = get_settings()
    catalog = ensure_diagnosis_suggestions_enabled()
    request_body = build_openai_request(payload, settings)
    try:
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {settings.openai_api_key.get_secret_value()}"},
            json=request_body,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        output_text = next(
            part["text"]
            for item in data.get("output", [])
            for part in item.get("content", [])
            if part.get("type") == "output_text"
        )
        generated = json.loads(output_text)["diagnoses"]
        validated = []
        seen = set()
        for item in generated:
            code = normalize_icd_code(item["code"])
            if code in catalog and code not in seen:
                validated.append({"code": code, "title": catalog[code]})
                seen.add(code)
        return DiagnosisSuggestionsOut(
            diagnoses=validated,
            model=settings.openai_model,
            generated_at=datetime.now(timezone.utc),
            request_id=str(uuid4()),
        )
    except (httpx.HTTPError, KeyError, StopIteration, TypeError, ValueError, json.JSONDecodeError, ValidationError) as exc:
        raise DiagnosisSuggestionUnavailable("AI prijedlog dijagnoza trenutačno nije dostupan.") from exc
