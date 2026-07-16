from app.models.domain import ClinicalFormDefinition, ClinicalFormInstance, ClinicalFormVersion, ServiceFormBinding
from app.services.clinical_forms import validate_data, validate_sections
from tests.conftest import login_token
from tests.factories import appointment


def headers(client):
    return {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}


def journey(client, db):
    appt = appointment(db)
    response = client.post("/api/patient-journeys", headers=headers(client), json={"appointment_id": appt.id, "intake_channel": "manual", "initial_stage": "booked"})
    assert response.status_code == 200
    return response.json()


def published_form(db, service_id):
    definition = ClinicalFormDefinition(form_key="synthetic-specialist", name="Sintetički pregled", specialty_key="general", activity_kind="specialist_consultation", active=True)
    db.add(definition); db.flush()
    version = ClinicalFormVersion(
        definition_id=definition.id,
        version=1,
        status="published",
        sections_json=[{"section_key": "main", "title": "Pregled", "fields": [
            {"field_key": "anamnesis", "label": "Anamneza", "type": "long_text", "required": True},
            {"field_key": "opinion", "label": "Mišljenje", "type": "long_text", "required": True},
            {"field_key": "diagnoses", "label": "Dijagnoze", "type": "diagnosis_list", "required": False},
        ]}],
        validation_schema_json={},
        print_layout_json={"layout": "clinical_report"},
        output_document_type="clinical_report",
    )
    db.add(version); db.flush()
    db.add(ServiceFormBinding(service_id=service_id, form_version_id=version.id, active=True))
    db.flush()
    return version


def test_missing_binding_fails_closed(client, db, auth_setup):
    visit = journey(client, db)
    activity = visit["activities"][0]
    response = client.post(f"/api/patient-journeys/{visit['id']}/activities/{activity['id']}/form/resolve", headers=headers(client))
    assert response.status_code == 409
    assert "nije konfiguriran" in response.json()["detail"]


def test_form_lifecycle_signing_and_controlled_amendment(client, db, auth_setup):
    visit = journey(client, db)
    activity = visit["activities"][0]
    published_form(db, activity["service_id"])
    base = f"/api/patient-journeys/{visit['id']}/activities/{activity['id']}/form"

    resolved = client.post(f"{base}/resolve", headers=headers(client))
    assert resolved.status_code == 200
    assert resolved.json()["binding_source"] == "default_service"
    assert resolved.json()["status"] == "draft"

    unknown = client.patch(base, headers=headers(client), json={"data": {"unsupported": "x"}})
    assert unknown.status_code == 422
    incomplete = client.patch(base, headers=headers(client), json={"data": {"anamnesis": "Sintetička anamneza"}})
    assert incomplete.status_code == 200
    assert client.post(f"{base}/complete", headers=headers(client)).status_code == 422

    saved = client.patch(base, headers=headers(client), json={"data": {"anamnesis": "Sintetička anamneza", "opinion": "Ljudsko mišljenje", "diagnoses": ["Z00.0"]}})
    assert saved.status_code == 200
    assert "Ljudsko mišljenje" in saved.json()["rendered_summary"]
    completed = client.post(f"{base}/complete", headers=headers(client))
    assert completed.status_code == 200 and completed.json()["status"] == "completed"
    signed = client.post(f"{base}/sign", headers=headers(client))
    assert signed.status_code == 200 and signed.json()["status"] == "signed"
    assert client.patch(base, headers=headers(client), json={"data": {"anamnesis": "Tiha izmjena"}}).status_code == 409

    amended = client.post(f"{base}/amend", headers=headers(client))
    assert amended.status_code == 200 and amended.json()["status"] == "draft"
    assert amended.json()["amended_from_instance_id"] == signed.json()["id"]
    assert amended.json()["data_json"]["opinion"] == "Ljudsko mišljenje"
    original = db.get(ClinicalFormInstance, signed.json()["id"])
    assert original.status == "amended"


def test_controlled_registry_rejects_duplicate_and_executable_fields():
    invalid_type = [{"section_key": "x", "fields": [{"field_key": "code", "label": "Code", "type": "javascript"}]}]
    try:
        validate_sections(invalid_type)
        assert False, "Executable field type must be rejected"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422


def test_repeatable_structured_group_requires_stable_ids_required_fields_and_unique_specimen_labels():
    sections = [{"section_key": "specimens", "fields": [{
        "field_key": "specimens", "label": "Uzorci", "type": "structured_specimen_list", "required": True, "max_items": 3,
        "item_fields": [
            {"field_key": "specimen_label", "label": "Oznaka", "type": "short_text", "required": True},
            {"field_key": "site", "label": "Mjesto", "type": "short_text", "required": True},
        ],
    }]}]
    validate_sections(sections)
    version = ClinicalFormVersion(sections_json=sections)
    valid = {"specimens": [
        {"item_id": "s1", "specimen_label": "A1", "site": "Antrum"},
        {"item_id": "s2", "specimen_label": "C1", "site": "Corpus"},
    ]}
    validate_data(version, valid)
    for invalid in [
        {"specimens": [{"specimen_label": "A1", "site": "Antrum"}]},
        {"specimens": [{"item_id": "same", "specimen_label": "A1", "site": "Antrum"}, {"item_id": "same", "specimen_label": "A2", "site": "Corpus"}]},
        {"specimens": [{"item_id": "s1", "specimen_label": "A1", "site": ""}]},
        {"specimens": [{"item_id": "s1", "specimen_label": "A1", "site": "Antrum"}, {"item_id": "s2", "specimen_label": "A1", "site": "Corpus"}]},
    ]:
        try:
            validate_data(version, invalid)
            assert False, f"Neispravan strukturirani unos mora biti odbijen: {invalid}"
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 422

    duplicate = [{"section_key": "x", "fields": [
        {"field_key": "same", "label": "One", "type": "short_text"},
        {"field_key": "same", "label": "Two", "type": "long_text"},
    ]}]
    try:
        validate_sections(duplicate)
        assert False, "Duplicate stable keys must be rejected"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422
