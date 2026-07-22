from datetime import datetime, timezone

from app.core.security import hash_password
from app.models.domain import Clinic, ClinicMembership, ClinicalFormDefinition, ClinicalFormInstance, ClinicalFormVersion, Institution, Patient, Role, ServiceFormBinding, SignedClinicalReport, User
from tests.conftest import login_token
from tests.factories import appointment


def headers(client):
    return {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}


def draft_payload(form: dict, data: dict) -> dict:
    return {"data": data, "expected_instance_id": form["id"], "expected_revision_number": form["revision_number"]}


def completion_payload(form: dict, key: str) -> dict:
    return {**draft_payload(form, form["data_json"]), "idempotency_key": key}


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
    resolved = client.post(f"{base}/resolve", headers=headers(client))
    assert resolved.status_code == 200
    saved = client.patch(base, headers=headers(client), json=draft_payload(resolved.json(), {"opinion": "Isključivo ljudski uneseno mišljenje."}))
    assert saved.status_code == 200
    assert client.post(f"{base}/complete", headers=headers(client), json=completion_payload(saved.json(), "signed-report-completion")).status_code == 200
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
    detail = client.get(f"/api/clinical-documents/{report.clinical_document_id}", headers=headers(client))
    assert detail.status_code == 200
    assert detail.json()["source_type"] == "generated_signed_report"
    assert detail.json()["document_type"] == "specialist_report"
    printed = client.post(f"/api/signed-reports/{report.id}/print", headers=headers(client))
    assert printed.status_code == 200
    assert printed.json()["report_id"] == report.id
    refreshed = client.get(f"/api/patient-journeys/{visit['id']}/visit-documents", headers=headers(client)).json()
    assert refreshed[0]["print_count"] == 1


def test_foreign_institution_cannot_list_deliver_or_read_report_history(client, db, auth_setup):
    visit, _, _, report = setup_signed_report(client, db)
    foreign_institution = Institution(code="foreign-report", name="Foreign report institution", active=True)
    foreign_clinic = Clinic(name="Foreign report clinic", institution_key="foreign-report", institution=foreign_institution)
    foreign_role = Role(
        name="foreign-report-doctor",
        description="Foreign report doctor",
        professional_category="medical_staff",
        permissions=[
            permission
            for permission in auth_setup["admin"].role.permissions
            if permission.name in {
                "clinical.documents.read_institution",
                "documents.view_source",
                "reports.read",
                "reports.send",
                "reports.delivery_history",
            }
        ],
    )
    foreign_user = User(
        email="foreign-report@test.local",
        full_name="Foreign Report Doctor",
        password_hash=hash_password("secret"),
        role=foreign_role,
    )
    db.add_all([foreign_clinic, foreign_role, foreign_user])
    db.flush()
    db.add(ClinicMembership(user_id=foreign_user.id, clinic_id=foreign_clinic.id, active=True, created_by_user_id=foreign_user.id))
    db.commit()
    foreign_headers = {"Authorization": f"Bearer {login_token(client, foreign_user.email)}"}

    assert client.get(f"/api/patient-journeys/{visit['id']}/visit-documents", headers=foreign_headers).status_code == 404
    assert client.get(f"/api/signed-reports/{report.id}", headers=foreign_headers).status_code == 404
    assert client.get(f"/api/signed-reports/{report.id}/delivery-history", headers=foreign_headers).status_code == 404
    delivered = client.post(
        f"/api/patient-journeys/{visit['id']}/visit-documents/deliver",
        headers=foreign_headers,
        json={"report_ids": [report.id], "recipient": "synthetic.patient@example.test"},
    )
    assert delivered.status_code == 404


def test_signed_report_has_no_mutation_api_and_generated_source_document_is_locked(client, db, auth_setup):
    _, _, _, report = setup_signed_report(client, db)

    patched_report = client.patch(f"/api/signed-reports/{report.id}", headers=headers(client), json={"title": "Nedopušteno"})
    deleted_report = client.delete(f"/api/signed-reports/{report.id}", headers=headers(client))
    patched_source = client.patch(
        f"/api/clinical-documents/{report.clinical_document_id}",
        headers=headers(client),
        json={"title": "Izmjena potpisanog izvora"},
    )

    assert patched_report.status_code == 405
    assert deleted_report.status_code == 405
    assert patched_source.status_code == 409
    assert patched_source.json()["detail"]["code"] == "signed_document_immutable"


def test_signed_report_snapshot_survives_later_form_instance_changes(client, db, auth_setup, sql_query_counter):
    _, _, _, report = setup_signed_report(client, db)
    original_content = report.rendered_content
    original_data = dict(report.structured_data_json)
    original_signer_user_id = report.signer_user_id
    original_signer_name = report.signer_name
    original_signed_at = report.signed_at
    original_form_version_id = report.form_version_id
    instance = db.get(ClinicalFormInstance, report.form_instance_id)
    template = db.get(ClinicalFormVersion, report.form_version_id)
    instance.rendered_summary = "Naknadna promjena obrasca koja ne smije izmijeniti potpisani nalaz"
    instance.data_json = {"opinion": "Naknadno promijenjeno"}
    template.sections_json = [{"section_key": "changed", "fields": []}]
    template.print_layout_json = {"layout": "naknadno-promijenjen-predlozak"}
    db.commit()

    request_headers = headers(client)
    with sql_query_counter.track() as query_count:
        preview = client.get(f"/api/signed-reports/{report.id}", headers=request_headers)

    assert preview.status_code == 200
    assert preview.json()["rendered_content"] == original_content
    assert preview.json()["structured_data_json"] == original_data
    assert "Naknadno" not in preview.json()["rendered_content"]
    assert preview.json()["signer_user_id"] == original_signer_user_id
    assert preview.json()["signer_name"] == original_signer_name
    assert preview.json()["signed_at"] == original_signed_at.isoformat().replace("+00:00", "Z")
    assert preview.json()["form_version_id"] == original_form_version_id
    assert query_count.count <= 12


def test_signed_report_addendum_is_separate_and_preserves_original_snapshot(client, db, auth_setup):
    _, _, _, report = setup_signed_report(client, db)
    original_content = report.rendered_content
    original_hash = report.content_hash

    addendum = client.post(
        f"/api/signed-reports/{report.id}/addenda",
        headers=headers(client),
        json={"reason": "Tipfeler u preporuci", "content": "Dopuna: pacijent dobiva ispravljenu administrativnu napomenu."},
    )

    db.refresh(report)
    assert addendum.status_code == 200
    assert addendum.json()["original_document_id"] == report.clinical_document_id
    assert addendum.json()["signed_report_id"] == report.id
    assert addendum.json()["original_document_type"] == "signed_clinical_report"
    assert addendum.json()["status"] == "signed"
    assert report.rendered_content == original_content
    assert report.content_hash == original_hash


def test_clinical_document_addendum_resolves_exact_signed_report_and_checks_integrity(client, db, auth_setup):
    _, _, _, report = setup_signed_report(client, db)

    linked = client.post(
        f"/api/clinical-documents/{report.clinical_document_id}/addenda",
        headers=headers(client),
        json={"reason": "Dopuna iz prikaza dokumenta", "content": "Odvojena dopuna vezana na točan nalaz."},
    )

    assert linked.status_code == 200
    assert linked.json()["signed_report_id"] == report.id
    assert linked.json()["original_document_type"] == "signed_clinical_report"

    report.rendered_content = "Neovlašteno promijenjen sadržaj"
    db.commit()
    rejected = client.post(
        f"/api/clinical-documents/{report.clinical_document_id}/addenda",
        headers=headers(client),
        json={"reason": "Ne smije proći", "content": "Integritet mora biti provjeren."},
    )
    assert rejected.status_code == 409


def test_signed_report_addendum_requires_intact_report_hash(client, db, auth_setup):
    _, _, _, report = setup_signed_report(client, db)
    report.content_hash = "tampered"
    db.commit()

    addendum = client.post(
        f"/api/signed-reports/{report.id}/addenda",
        headers=headers(client),
        json={"reason": "Pokušaj dopune", "content": "Ovo ne smije proći jer integritet nije potvrđen."},
    )

    assert addendum.status_code == 409


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
    saved_amendment = client.patch(base, headers=headers(client), json=draft_payload(amendment, {"opinion": "Kontrolirani ispravak."}))
    assert saved_amendment.status_code == 200
    assert client.post(f"{base}/complete", headers=headers(client), json=completion_payload(saved_amendment.json(), "amendment-completion")).status_code == 200
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
