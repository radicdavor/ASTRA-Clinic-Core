from pydantic import SecretStr

from app.core.config import Settings
from app.schemas.journey_encounter import DiagnosisSuggestionRequest
from app.services import encounter_diagnosis


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"output": [{"content": [{"type": "output_text", "text": '{"diagnoses":[{"code":"K21.9","title":"Untrusted label"},{"code":"X99.9","title":"Unknown"}]}'}]}]}


def settings(**overrides):
    return Settings(openai_api_key=SecretStr("test-key"), ai_diagnosis_suggestions_enabled=True, **overrides)


def test_capability_requires_explicit_flag_key_and_catalog(monkeypatch):
    monkeypatch.setattr(encounter_diagnosis, "get_icd10_catalog", lambda: None)
    assert encounter_diagnosis.diagnosis_suggestions_capability(settings())["enabled"] is False
    assert encounter_diagnosis.diagnosis_suggestions_capability(Settings())["enabled"] is False
    assert "katalog" in str(encounter_diagnosis.diagnosis_suggestions_capability(settings())["reason"]).lower()


def test_enabled_mocked_provider_uses_catalog_label_and_rejects_unknown_code(monkeypatch):
    configured = settings()
    monkeypatch.setattr(encounter_diagnosis, "get_settings", lambda: configured)
    monkeypatch.setattr(encounter_diagnosis, "get_icd10_catalog", lambda: {"K21.9": "Kanonski naziv"})
    monkeypatch.setattr(encounter_diagnosis.httpx, "post", lambda *args, **kwargs: FakeResponse())
    result = encounter_diagnosis.suggest_icd10_diagnoses(DiagnosisSuggestionRequest(anamnesis="Sintetičke tegobe"))
    assert [(item.code, item.title) for item in result.diagnoses] == [("K21.9", "Kanonski naziv")]


def test_request_builder_contains_only_clinical_text_and_store_false():
    request = encounter_diagnosis.build_openai_request(
        DiagnosisSuggestionRequest(anamnesis="Sintetička anamneza", opinion="Sintetičko mišljenje"),
        settings(),
    )
    assert request["store"] is False
    assert set(request) == {"model", "store", "max_output_tokens", "instructions", "input", "text"}
    assert "patient" not in str(request).lower()
    assert "appointment" not in str(request).lower()
    assert "date_of_birth" not in str(request).lower()


def test_production_settings_reject_unapproved_ai_diagnosis_enablement():
    configured = settings(
        app_env="production",
        jwt_secret="x" * 40,
        cors_origins="https://clinic.example",
        cors_origin_regex=None,
    )
    try:
        configured.validate_production_safety()
    except RuntimeError as exc:
        assert "separate explicit production authorization" in str(exc)
    else:
        raise AssertionError("Unsafe production AI configuration was accepted")
