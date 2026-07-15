import json
from datetime import datetime, timezone

import httpx
from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.journey_encounter import DiagnosisSuggestionRequest, DiagnosisSuggestionsOut


class DiagnosisSuggestionUnavailable(RuntimeError):
    pass


def suggest_icd10_diagnoses(payload: DiagnosisSuggestionRequest) -> DiagnosisSuggestionsOut:
    settings = get_settings()
    if not settings.openai_api_key:
        raise DiagnosisSuggestionUnavailable("OpenAI nije konfiguriran.")

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
    request_body = {
        "model": settings.openai_model,
        "store": False,
        "max_output_tokens": 500,
        "instructions": (
            "Ti si medicinski pisani asistent liječniku u Hrvatskoj. Na temelju isključivo dostavljenog teksta "
            "predloži najviše pet mogućih dijagnoza s WHO ICD-10 šiframa i hrvatskim nazivima. Ne donosi konačnu "
            "dijagnozu i ne dodaj podatke kojih nema. Ako podaci nisu dovoljni, vrati prazan niz."
        ),
        "input": clinical_text,
        "text": {"format": {"type": "json_schema", "name": "icd10_suggestions", "strict": True, "schema": schema}},
    }
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
        diagnoses = json.loads(output_text)["diagnoses"]
        return DiagnosisSuggestionsOut(
            diagnoses=diagnoses,
            model=settings.openai_model,
            generated_at=datetime.now(timezone.utc),
        )
    except (httpx.HTTPError, KeyError, StopIteration, TypeError, ValueError, json.JSONDecodeError, ValidationError) as exc:
        raise DiagnosisSuggestionUnavailable("AI prijedlog dijagnoza trenutačno nije dostupan.") from exc
