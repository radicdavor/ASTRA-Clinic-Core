from datetime import datetime, timezone

from app.models.domain import ClinicalFormDefinition, ClinicalFormVersion, Patient, ServiceFormBinding, SignedClinicalReport
from tests.conftest import login_token
from tests.factories import appointment


def headers(client):
    return {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}


def setup_signed_report(client, db):
    appt = appointment(db)
    patient = db.get(Patient, appt.patient_id)
    patient.email = "synthetic.patient@example.test"
    patient.email_verified_at = datetime.now(timezone.utc)
    db.flush()
    visit = client.post("/api/patient-journeys", headers=headers(client), json={"appointment_id": appt.id, "intake_channel": "manual", "initial_stage": "booked"}).json()
    activity = visit["activities"][0]
    definition = ClinicalFormDefinition(form_key="signed-report-test", name="Sintetički pregled", specialty_key="general", activity_kind="specialist_consultation", active=True)
    db.add(definition); db.flush()
    version = ClinicalFormVersion(
        definition_id=definition.id, version=1, status="published",
        sections_json=[{"section_key": "main", "title": "Nalaz", "fields": [{"field_key": "opinion", "label": "Mišljenje", "type": "long_text", "required": True}]}],
        validation_schema_json={}, print_layout_json={"layout": "clinical_report"}, output_document_type="specialist_report",
    )
    db.add(version); db.flush()
    db.add(ServiceFormBinding(service_id=activity["service_id"], form_version_id=version.id, active=True)); db.flush()
    base = f"/api/patient-journeys/{visit['id']}/activities/{activity['id']}/form"
    assert client.post(f"{base}/resolve", headers=headers(client)).status_code == 200
    saved = client.patch(base, headers=headers(client), json={"data": {"opinion": "Isključivo ljudski uneseno mišljenje."}})
    assert saved.status_code == 200
    assert client.post(f"{base}/complete", headers=headers(client), json={"data": saved.json()["data_json"], "expected_revision_number": saved.json()["revision_number"]}).status_code == 200
    signed = client.post(f"{base}/sign", headers=headers(client))
    assert signed.status_code == 200
    report = db.query(SignedClinicalReport).filter_by(form_instance_id=signed.json()["id"]).one()
    return visit, activity, base, report


def test_signing_creates_immutable_clinical_document_and_print_history(client, db, auth_setup):
    visit, _, _, report = setup_signed_report(client, db)
    documents = client.get(f"/api/patient-journeys/{visit['id']}/visit-documents", headers=headers(client))
    assert documents.status_code == 200
    assert documents.json()[0]["report"]["clinical_document_id"] == report.clinical_document_id
    assert documents.json()[0]["report"]["rendered_content"] == "Mišljenje: Isključivo ljudski uneseno mišljenje."
    printed = client.post(f"/api/signed-reports/{report.id}/print", headers=headers(client))
    assert printed.status_code == 200
    assert printed.json()["report_id"] == report.id
    refreshed = client.get(f"/api/patient-journeys/{visit['id']}/visit-documents", headers=headers(client)).json()
    assert refreshed[0]["print_count"] == 1


def test_delivery_is_explicit_stub_and_amendment_preserves_original(client, db, auth_setup):
    visit, _, base, report = setup_signed_report(client, db)
    delivered = client.post(
        f"/api/patient-journeys/{visit['id']}/visit-documents/deliver",
        headers=headers(client),
        json={"report_ids": [report.id], "recipient": "synthetic.patient@example.test"},
    )
    assert delivered.status_code == 200
    assert delivered.json()[0]["status"] == "queued_stub"
    assert delivered.json()[0]["sent_at"] is None
    assert delivered.json()[0]["delivered_at"] is None

    amendment = client.post(f"{base}/amend", headers=headers(client)).json()
    saved_amendment = client.patch(base, headers=headers(client), json={"data": {"opinion": "Kontrolirani ispravak."}})
    assert saved_amendment.status_code == 200
    assert client.post(f"{base}/complete", headers=headers(client), json={"data": saved_amendment.json()["data_json"], "expected_revision_number": saved_amendment.json()["revision_number"]}).status_code == 200
    assert client.post(f"{base}/sign", headers=headers(client)).status_code == 200
    reports = db.query(SignedClinicalReport).filter_by(journey_id=visit["id"]).order_by(SignedClinicalReport.version_number).all()
    assert len(reports) == 2
    assert reports[0].rendered_content == "Mišljenje: Isključivo ljudski uneseno mišljenje."
    assert reports[0].superseded_at is not None
    assert reports[1].supersedes_report_id == reports[0].id
    assert reports[1].form_instance_id == amendment["id"]

    blocked = client.post(
        f"/api/patient-journeys/{visit['id']}/visit-documents/deliver",
        headers=headers(client),
        json={"report_ids": [reports[0].id], "recipient": "synthetic.patient@example.test"},
    )
    assert blocked.status_code == 409
