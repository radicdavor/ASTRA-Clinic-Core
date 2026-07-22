from datetime import date, time
from decimal import Decimal

import pytest

from app.models.domain import (
    ApiKey,
    Appointment,
    AuditLog,
    Clinic,
    ClinicMembership,
    ClinicalDocument,
    ClinicalEpisode,
    ClinicalFinding,
    ClinicalOpenQuestion,
    ClinicalPlan,
    Institution,
    Invoice,
    InvoiceLine,
    Patient,
    PatientClinicAssociation,
    PaymentTransaction,
    Provider,
    Room,
    Service,
)
from app.auth.dependencies import hash_api_key
from tests.conftest import login_token


BLOCKER_XFAIL = pytest.mark.xfail(
    strict=True,
    reason="PR #3 cross-scope blocker reproduced; remove xfail with the scoped remediation",
)


def _headers(client, auth_setup) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {login_token(client, 'admin@test.local')}",
        "X-Clinic-Id": str(auth_setup["clinic"].id),
    }


def _two_institution_patient(db, auth_setup):
    clinic_a = auth_setup["clinic"]
    institution_b = Institution(code="scope-b", name="Scope Institution B", active=True)
    clinic_b = Clinic(name="Scope Clinic B", institution_key="scope-b", institution=institution_b)
    patient = Patient(first_name="Scope", last_name="Synthetic")
    db.add_all([institution_b, clinic_b, patient])
    db.flush()
    db.add_all(
        [
            PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic_a.id, active=True),
            PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic_b.id, active=True),
        ]
    )
    db.flush()
    return clinic_a, clinic_b, patient


def _foreign_invoice(db, auth_setup, *, status: str = "issued"):
    clinic_a, clinic_b, patient = _two_institution_patient(db, auth_setup)
    invoice = Invoice(
        patient_id=patient.id,
        clinic_id=clinic_b.id,
        invoice_number=f"FOREIGN-{status.upper()}",
        status=status,
        payment_status="unpaid",
        total_amount=Decimal("100"),
    )
    db.add(invoice)
    db.flush()
    line = InvoiceLine(
        invoice_id=invoice.id,
        description="Scoped service",
        quantity=Decimal("1"),
        unit_price=Decimal("100"),
        total=Decimal("100"),
    )
    payment = PaymentTransaction(
        invoice_id=invoice.id,
        amount=Decimal("10"),
        method="cash",
    )
    db.add_all([line, payment])
    db.flush()
    return clinic_a, clinic_b, patient, invoice


@pytest.mark.parametrize("operation", ["detail", "update", "issue", "payment_create", "payment_list"])
def test_foreign_clinic_invoice_operations_are_non_enumerating(client, db, auth_setup, operation):
    status = "draft" if operation == "issue" else "issued"
    _, _, patient, invoice = _foreign_invoice(db, auth_setup, status=status)
    headers = _headers(client, auth_setup)

    if operation == "detail":
        response = client.get(f"/api/invoices/{invoice.id}", headers=headers)
    elif operation == "update":
        response = client.patch(
            f"/api/invoices/{invoice.id}",
            headers=headers,
            json={"patient_id": patient.id, "notes": "FOREIGN_BILLING_SENTINEL"},
        )
    elif operation == "issue":
        response = client.post(f"/api/invoices/{invoice.id}/issue", headers=headers)
    elif operation == "payment_create":
        response = client.post(
            f"/api/invoices/{invoice.id}/payments",
            headers=headers,
            json={"amount": "10", "method": "cash"},
        )
    else:
        response = client.get(f"/api/invoices/{invoice.id}/payments", headers=headers)

    assert response.status_code == 404


@pytest.mark.parametrize("operation", ["line_list", "line_create", "line_update", "line_delete", "mark_paid"])
def test_foreign_clinic_invoice_child_operations_are_non_enumerating(client, db, auth_setup, operation):
    _, _, _, invoice = _foreign_invoice(db, auth_setup)
    line = invoice.lines[0]
    headers = _headers(client, auth_setup)
    if operation == "line_list":
        response = client.get(f"/api/invoices/{invoice.id}/lines", headers=headers)
    elif operation == "line_create":
        response = client.post(
            f"/api/invoices/{invoice.id}/lines",
            headers=headers,
            json={"description": "Foreign line", "quantity": "1", "unit_price": "10"},
        )
    elif operation == "line_update":
        response = client.patch(
            f"/api/invoices/{invoice.id}/lines/{line.id}",
            headers=headers,
            json={"description": "Foreign mutation"},
        )
    elif operation == "line_delete":
        response = client.delete(f"/api/invoices/{invoice.id}/lines/{line.id}", headers=headers)
    else:
        response = client.post(f"/api/invoices/{invoice.id}/mark-paid", headers=headers)
    assert response.status_code == 404


def test_invoice_list_and_clinic_switch_use_only_active_clinic(client, db, auth_setup):
    clinic_a, clinic_b, patient = _two_institution_patient(db, auth_setup)
    db.add(ClinicMembership(user_id=auth_setup["admin"].id, clinic_id=clinic_b.id, active=True))
    local = Invoice(patient_id=patient.id, clinic_id=clinic_a.id, invoice_number="LOCAL-LIST", status="draft")
    foreign = Invoice(patient_id=patient.id, clinic_id=clinic_b.id, invoice_number="FOREIGN-LIST", status="draft")
    db.add_all([local, foreign])
    db.flush()
    token = login_token(client, "admin@test.local")

    local_response = client.get(
        "/api/invoices",
        headers={"Authorization": f"Bearer {token}", "X-Clinic-Id": str(clinic_a.id)},
    )
    foreign_response = client.get(
        "/api/invoices",
        headers={"Authorization": f"Bearer {token}", "X-Clinic-Id": str(clinic_b.id)},
    )
    assert {item["id"] for item in local_response.json()} == {local.id}
    assert {item["id"] for item in foreign_response.json()} == {foreign.id}


def test_billing_permission_without_clinic_membership_is_denied(client, auth_setup):
    token = login_token(client, "limited@test.local")
    response = client.get("/api/invoices", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_billing_api_key_cannot_select_a_clinic(client, db):
    raw_key = "scope-billing-api-key"
    db.add(ApiKey(name="Billing machine", key_hash=hash_api_key(raw_key), scopes=["billing.read"], active=True))
    db.flush()
    response = client.get("/api/invoices", headers={"X-ASTRA-API-Key": raw_key, "X-Clinic-Id": "1"})
    assert response.status_code == 403


def _foreign_episode(db, auth_setup):
    clinic_a, clinic_b, patient = _two_institution_patient(db, auth_setup)
    provider = Provider(full_name="dr. Scope B", specialty="Gastroenterology", clinic=clinic_b)
    room = Room(name="Scope B Room", type="ordination", clinic=clinic_b)
    service = Service(name="Scope B Service", duration_minutes=30, price=Decimal("100"))
    episode_kwargs = {
        "patient_id": patient.id,
        "title": "FOREIGN_EPISODE_SENTINEL",
        "episode_type": "gastroenterology",
        "status": "active",
        "priority": "routine",
        "start_date": date(2026, 7, 22),
        "summary": "FOREIGN_EPISODE_SUMMARY",
        "clinical_notes": "FOREIGN_EPISODE_NOTE",
    }
    if hasattr(ClinicalEpisode, "institution_id"):
        episode_kwargs["institution_id"] = clinic_b.institution_id
    episode = ClinicalEpisode(**episode_kwargs)
    db.add_all([provider, room, service, episode])
    db.flush()
    appointment = Appointment(
        patient_id=patient.id,
        provider_id=provider.id,
        room_id=room.id,
        clinic_id=clinic_b.id,
        service_id=service.id,
        episode_id=episode.id,
        date=date(2026, 7, 22),
        start_time=time(9),
        end_time=time(9, 30),
        duration_minutes=30,
        status="scheduled",
        source="manual",
    )
    plan = ClinicalPlan(
        episode_id=episode.id,
        source="manual",
        status="draft",
        next_action="follow_up_visit",
        priority="routine",
        rationale="FOREIGN_PLAN_SENTINEL",
    )
    db.add_all([appointment, plan])
    db.flush()
    return patient, episode, plan


@pytest.mark.parametrize(
    "operation",
    [
        "list",
        "patient_list",
        "detail",
        "update",
        "close",
        "appointments",
        "plans",
        "plan_update",
        "plan_reject",
        "plan_confirm",
        "timeline",
    ],
)
def test_foreign_institution_episode_and_plan_operations_are_denied(client, db, auth_setup, operation):
    patient, episode, plan = _foreign_episode(db, auth_setup)
    headers = _headers(client, auth_setup)

    if operation == "list":
        response = client.get("/api/episodes", headers=headers)
        assert episode.id not in {item["id"] for item in response.json()}
        return
    if operation == "patient_list":
        response = client.get(f"/api/patients/{patient.id}/episodes", headers=headers)
        assert episode.id not in {item["id"] for item in response.json()}
        return
    if operation == "detail":
        response = client.get(f"/api/episodes/{episode.id}", headers=headers)
    elif operation == "update":
        response = client.patch(
            f"/api/episodes/{episode.id}",
            headers=headers,
            json={"clinical_notes": "FOREIGN_EPISODE_MUTATION"},
        )
    elif operation == "close":
        response = client.post(f"/api/episodes/{episode.id}/close", headers=headers)
    elif operation == "appointments":
        response = client.get(f"/api/episodes/{episode.id}/appointments", headers=headers)
    elif operation == "plans":
        response = client.get(f"/api/episodes/{episode.id}/clinical-plans", headers=headers)
    elif operation == "plan_update":
        response = client.patch(
            f"/api/clinical-plans/{plan.id}",
            headers=headers,
            json={"rationale": "FOREIGN_PLAN_MUTATION"},
        )
    elif operation == "plan_reject":
        response = client.post(f"/api/clinical-plans/{plan.id}/reject", headers=headers)
    elif operation == "plan_confirm":
        response = client.post(f"/api/clinical-plans/{plan.id}/confirm", headers=headers)
    else:
        response = client.get(f"/api/episodes/{episode.id}/clinical-timeline", headers=headers)
    assert response.status_code == 404


def test_unresolved_legacy_episode_is_hidden(client, db, auth_setup):
    patient = Patient(first_name="Legacy", last_name="Unresolved")
    db.add(patient)
    db.flush()
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=auth_setup["clinic"].id, active=True))
    episode = ClinicalEpisode(
        patient_id=patient.id,
        institution_id=None,
        title="UNRESOLVED_EPISODE_SENTINEL",
        status="active",
        priority="routine",
        start_date=date(2026, 7, 22),
    )
    db.add(episode)
    db.flush()
    response = client.get(f"/api/episodes/{episode.id}", headers=_headers(client, auth_setup))
    assert response.status_code == 404


def test_episode_api_key_permission_has_no_implicit_institution_scope(client, db):
    raw_key = "scope-episode-api-key"
    db.add(ApiKey(name="Episode machine", key_hash=hash_api_key(raw_key), scopes=["episodes.read"], active=True))
    db.flush()
    response = client.get("/api/episodes", headers={"X-ASTRA-API-Key": raw_key, "X-Clinic-Id": "1"})
    assert response.status_code == 403


def _foreign_derived_data(db, auth_setup):
    _, clinic_b, patient = _two_institution_patient(db, auth_setup)
    document = ClinicalDocument(
        patient_id=patient.id,
        clinic_id=clinic_b.id,
        institution_id=clinic_b.institution_id,
        source_type="upload",
        document_type="external_report",
        title="Scope B source",
        is_clinical_record=True,
        record_classification="clinical",
        review_status="reviewed",
        physician_reviewed=True,
    )
    db.add(document)
    db.flush()
    finding_kwargs = {
        "patient_id": patient.id,
        "source_document_id": document.id,
        "source_type": "clinical_document",
        "source_label": "Scope B finding source",
        "source_reference": f"clinical_document:{document.id}",
        "finding_key": "scope_b_finding",
        "label": "FOREIGN_FINDING_SENTINEL",
        "category": "test",
        "lifecycle_status": "awaiting_review",
        "requires_review": True,
    }
    if hasattr(ClinicalFinding, "institution_id"):
        finding_kwargs["institution_id"] = clinic_b.institution_id
    finding = ClinicalFinding(**finding_kwargs)
    db.add(finding)
    db.flush()
    question_kwargs = {
        "patient_id": patient.id,
        "finding_id": finding.id,
        "source_document_id": document.id,
        "source_type": "clinical_document",
        "source_label": "Scope B question source",
        "source_reference": f"clinical_document:{document.id}",
        "question_key": "scope_b_question",
        "label": "FOREIGN_QUESTION_SENTINEL",
        "status": "awaiting_review",
        "requires_clinician_review": True,
    }
    if hasattr(ClinicalOpenQuestion, "institution_id"):
        question_kwargs["institution_id"] = clinic_b.institution_id
    question = ClinicalOpenQuestion(**question_kwargs)
    db.add(question)
    db.flush()
    return patient, finding, question


@pytest.mark.parametrize("operation", ["finding_list", "finding_detail", "question_list", "question_detail", "timeline"])
def test_foreign_institution_derived_clinical_data_is_hidden(client, db, auth_setup, operation):
    patient, finding, question = _foreign_derived_data(db, auth_setup)
    headers = _headers(client, auth_setup)
    if operation == "finding_list":
        response = client.get(f"/api/patients/{patient.id}/clinical-findings", headers=headers)
        assert finding.id not in {item["id"] for item in response.json()["findings"]}
        return
    if operation == "finding_detail":
        response = client.get(f"/api/patients/{patient.id}/clinical-findings/{finding.id}", headers=headers)
    elif operation == "question_list":
        response = client.get(f"/api/patients/{patient.id}/clinical-open-questions", headers=headers)
        assert question.id not in {item["id"] for item in response.json()["questions"]}
        return
    elif operation == "question_detail":
        response = client.get(f"/api/patients/{patient.id}/clinical-open-questions/{question.id}", headers=headers)
    else:
        response = client.get(f"/api/patients/{patient.id}/clinical-evidence-timeline", headers=headers)
        keys = {item["event_key"] for item in response.json()["events"]}
        assert f"clinical_finding:{finding.id}" not in keys
        assert f"clinical_open_question:{question.id}" not in keys
        return
    assert response.status_code == 404


def test_unresolved_legacy_derived_clinical_data_is_hidden(client, db, auth_setup):
    patient = Patient(first_name="Legacy", last_name="Derived")
    db.add(patient)
    db.flush()
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=auth_setup["clinic"].id))
    finding = ClinicalFinding(
        patient_id=patient.id,
        institution_id=None,
        source_type="legacy",
        source_label="Unresolved legacy source",
        source_reference="legacy:unresolved",
        finding_key="unresolved_legacy_finding",
        label="UNRESOLVED_FINDING_SENTINEL",
        category="test",
        lifecycle_status="awaiting_review",
        requires_review=True,
    )
    db.add(finding)
    db.flush()
    question = ClinicalOpenQuestion(
        patient_id=patient.id,
        institution_id=None,
        finding_id=finding.id,
        source_type="legacy",
        source_label="Unresolved legacy source",
        source_reference="legacy:unresolved",
        question_key="unresolved_legacy_question",
        label="UNRESOLVED_QUESTION_SENTINEL",
        status="awaiting_review",
        requires_clinician_review=True,
    )
    db.add(question)
    db.flush()

    headers = _headers(client, auth_setup)
    findings = client.get(f"/api/patients/{patient.id}/clinical-findings", headers=headers)
    questions = client.get(f"/api/patients/{patient.id}/clinical-open-questions", headers=headers)
    timeline = client.get(f"/api/patients/{patient.id}/clinical-evidence-timeline", headers=headers)

    assert findings.status_code == questions.status_code == timeline.status_code == 200
    assert findings.json()["findings"] == []
    assert questions.json()["questions"] == []
    assert timeline.json()["events"] == []


@BLOCKER_XFAIL
def test_audit_log_is_clinic_scoped_and_returns_phi_safe_projection(client, db, auth_setup):
    clinic_a, clinic_b, _ = _two_institution_patient(db, auth_setup)
    common = {"action": "update", "entity_type": "ClinicalDocument", "entity_id": 999}
    local_kwargs = dict(common)
    foreign_kwargs = dict(common)
    if hasattr(AuditLog, "clinic_id"):
        local_kwargs.update(clinic_id=clinic_a.id, institution_id=clinic_a.institution_id)
        foreign_kwargs.update(clinic_id=clinic_b.id, institution_id=clinic_b.institution_id)
    local = AuditLog(
        **local_kwargs,
        summary="Local safe event",
        after_json={"raw_text": "AUDIT_PHI_SENTINEL", "token": "SESSION_SECRET_SENTINEL"},
    )
    foreign = AuditLog(
        **foreign_kwargs,
        summary="Foreign event",
        after_json={"report_content": "REPORT_CONTENT_SENTINEL"},
    )
    db.add_all([local, foreign])
    db.flush()

    response = client.get("/api/audit-log", headers=_headers(client, auth_setup))
    assert response.status_code == 200
    payload = response.json()
    assert foreign.id not in {item["id"] for item in payload}
    serialized = response.text
    assert "AUDIT_PHI_SENTINEL" not in serialized
    assert "SESSION_SECRET_SENTINEL" not in serialized
    assert "REPORT_CONTENT_SENTINEL" not in serialized
