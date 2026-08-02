from datetime import date

from app.core.security import hash_password
from app.auth.dependencies import hash_api_key
from app.models.domain import ApiKey, AuditLog, Clinic, ClinicMembership, Institution, Patient, PatientClinicAssociation, Permission, Role, User
from app.schemas.common import PatientCreate
from app.services.patient_identity_reconciliation import candidate_reasons, identity_snapshot, normalized_identity
from tests.conftest import login_token


def _auth_headers(client) -> dict[str, str]:
    return {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}


def _reviewer_headers(client, db) -> dict[str, str]:
    permission = db.query(Permission).filter_by(name="patients.identity_reconciliation.review").first()
    if permission is None:
        permission = Permission(name="patients.identity_reconciliation.review", description="review")
    role = Role(name="identity-reviewer-test", description="Identity reviewer", permissions=[permission])
    reviewer = User(email="identity.reviewer@test.local", full_name="Identity Reviewer", password_hash=hash_password("secret"), role=role)
    db.add_all([role, reviewer]); db.commit()
    return {"Authorization": f"Bearer {login_token(client, reviewer.email)}"}


def _request(client, **overrides):
    payload = {"first_name": "Ana", "last_name": "Horvat", "date_of_birth": "1987-04-03", "email": "ana.foreign@example.com", "phone": "+385 91 222 3333"}
    payload.update(overrides)
    return client.post("/api/patients", headers=_auth_headers(client), json=payload)


def _foreign_patient(db, *, oib: str | None = None) -> Patient:
    suffix = db.query(Patient).count() + 1
    institution = Institution(code=f"identity-b-{suffix}", name=f"Synthetic Identity Institution B {suffix}", active=True)
    clinic = Clinic(name=f"Synthetic Identity Clinic B1 {suffix}", institution_key=f"identity-b-{suffix}", institution=institution)
    patient = Patient(
        first_name="  ANA ",
        last_name=" HORVAT  ",
        date_of_birth=date(1987, 4, 3),
        oib=oib,
        email="ana.foreign@example.com",
        phone="+385 91 222 3333",
    )
    db.add_all([institution, clinic, patient])
    db.flush()
    db.add(PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic.id, active=True))
    db.commit()
    return patient


def test_cross_tenant_non_oib_collision_creates_opaque_review_without_duplicate(client, db, auth_setup):
    foreign = _foreign_patient(db)
    before = db.query(Patient).count()

    response = client.post(
        "/api/patients",
        headers=_auth_headers(client),
        json={
            "first_name": "Ana",
            "last_name": "Horvat",
            "date_of_birth": "1987-04-03",
            "email": "ana.foreign@example.com",
            "phone": "+385 91 222 3333",
        },
    )

    assert response.status_code == 202
    assert db.query(Patient).count() == before
    body = response.json()
    assert body["code"] == "patient_identity_review_required"
    assert body["status"] == "pending_review"
    serialized = response.text.lower()
    assert "candidate_patient_id" not in serialized
    assert "candidate" not in serialized
    assert "match_reason" not in serialized
    assert "identity-b" not in serialized


def test_cross_tenant_oib_collision_has_durable_linking_request(client, db, auth_setup):
    foreign = _foreign_patient(db, oib="12345678901")

    response = client.post(
        "/api/patients",
        headers=_auth_headers(client),
        json={
            "first_name": "Ana",
            "last_name": "Horvat",
            "date_of_birth": "1987-04-03",
            "oib": "12345678901",
        },
    )

    assert response.status_code == 202
    request_id = response.json()["request_id"]
    status_response = client.get(f"/api/patient-identity-reconciliations/{request_id}", headers=_auth_headers(client))
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "pending_review"
    assert not db.query(PatientClinicAssociation).filter_by(
        patient_id=foreign.id,
        clinic_id=auth_setup["clinic"].id,
    ).first()
    reviewer = _reviewer_headers(client, db)
    distinct = client.post(
        f"/api/patient-identity-reconciliations/review/{request_id}/confirm-distinct",
        headers=reviewer,
        json={"reason": "Synthetic evidence cannot override global OIB uniqueness"},
    )
    assert distinct.status_code == 409
    assert db.query(Patient).filter_by(oib="12345678901").count() == 1


def test_matcher_requires_approved_exact_combinations():
    patient = Patient(first_name=" Ana ", last_name="HORVAT", date_of_birth=date(1987, 4, 3), oib="12345678901", email="ANA@EXAMPLE.COM", phone="+385 (91) 222-3333")
    strong = normalized_identity(identity_snapshot(PatientCreate(first_name="ana", last_name="horvat", date_of_birth=date(1987, 4, 3), oib="12345678901", email="ana@example.com", phone="+385912223333")))
    assert set(candidate_reasons(patient, strong)) == {"oib", "name_date_of_birth", "date_of_birth_email", "date_of_birth_phone"}
    weak = normalized_identity(identity_snapshot(PatientCreate(first_name="X", last_name="Y", email="ana@example.com", phone="+385912223333")))
    assert candidate_reasons(patient, weak) == []


def test_reviewer_permission_is_explicit_and_link_is_idempotent(client, db, auth_setup):
    foreign = _foreign_patient(db)
    request_id = _request(client).json()["request_id"]
    assert client.get("/api/patient-identity-reconciliations/review/pending", headers=_auth_headers(client)).status_code == 403
    reviewer = _reviewer_headers(client, db)
    detail = client.get(f"/api/patient-identity-reconciliations/review/{request_id}", headers=reviewer)
    assert detail.status_code == 200
    assert detail.json()["candidates"][0]["patient_id"] == foreign.id
    assert "ana.foreign@example.com" not in detail.text.lower()
    assert "+385 91 222 3333" not in detail.text
    decision = {"reason": "Verified synthetic identity evidence", "candidate_patient_id": foreign.id}
    approved = client.post(f"/api/patient-identity-reconciliations/review/{request_id}/approve-link", headers=reviewer, json=decision)
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved_link"
    assert db.query(PatientClinicAssociation).filter_by(patient_id=foreign.id, clinic_id=auth_setup["clinic"].id).count() == 1
    replay = client.post(f"/api/patient-identity-reconciliations/review/{request_id}/approve-link", headers=reviewer, json=decision)
    assert replay.status_code == 409
    assert db.query(PatientClinicAssociation).filter_by(patient_id=foreign.id, clinic_id=auth_setup["clinic"].id).count() == 1


def test_confirm_distinct_creates_one_patient_and_reject_creates_none(client, db, auth_setup):
    _foreign_patient(db)
    reviewer = _reviewer_headers(client, db)
    before = db.query(Patient).count()
    request_id = _request(client).json()["request_id"]
    result = client.post(f"/api/patient-identity-reconciliations/review/{request_id}/confirm-distinct", headers=reviewer, json={"reason": "Synthetic evidence proves a distinct person"})
    assert result.status_code == 200
    assert result.json()["status"] == "confirmed_distinct"
    assert db.query(Patient).count() == before + 1
    assert db.query(PatientClinicAssociation).filter_by(patient_id=result.json()["result_patient_id"], clinic_id=auth_setup["clinic"].id).count() == 1

    _foreign_patient(db, oib="98765432109")
    rejected_id = _request(client, first_name="Iva", last_name="Kovač", date_of_birth="1992-06-07", oib="98765432109", email=None, phone=None).json()["request_id"]
    count = db.query(Patient).count()
    rejected = client.post(f"/api/patient-identity-reconciliations/review/{rejected_id}/reject", headers=reviewer, json={"reason": "Insufficient synthetic identity evidence"})
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected_insufficient_evidence"
    assert db.query(Patient).count() == count


def test_requester_status_is_clinic_scoped_and_audit_contains_no_identity_pii(client, db, auth_setup):
    _foreign_patient(db, oib="12345678901")
    request_id = _request(client, oib="12345678901").json()["request_id"]
    other_institution = Institution(code="requester-c", name="Synthetic Requester Institution C", active=True)
    other_clinic = Clinic(name="Synthetic Requester Clinic C1", institution_key="requester-c", institution=other_institution)
    existing_permission = db.query(Permission).filter_by(name="patients.write").one()
    role = Role(name="foreign-requester", description="Foreign requester", permissions=[existing_permission])
    user = User(email="foreign.requester@test.local", full_name="Foreign Requester", password_hash=hash_password("secret"), role=role)
    db.add_all([other_institution, other_clinic, role, user]); db.flush()
    db.add(ClinicMembership(user_id=user.id, clinic_id=other_clinic.id, active=True, created_by_user_id=user.id)); db.commit()
    foreign_headers = {"Authorization": f"Bearer {login_token(client, user.email)}"}
    assert client.get(f"/api/patient-identity-reconciliations/{request_id}", headers=foreign_headers).status_code == 404
    audit_text = " ".join(f"{item.before_json} {item.after_json} {item.summary}" for item in db.query(AuditLog).all())
    assert "12345678901" not in audit_text
    assert "ana.foreign@example.com" not in audit_text.lower()


def test_api_key_cannot_become_reviewer_and_match_kinds_are_equally_opaque(client, db, auth_setup):
    _foreign_patient(db, oib="12345678901")
    oib_response = _request(client, first_name="Iva", last_name="Kovač", date_of_birth="1990-01-01", oib="12345678901", email=None, phone=None)
    _foreign_patient(db)
    non_oib_response = _request(client)
    assert set(oib_response.json()) == set(non_oib_response.json()) == {"code", "request_id", "status", "message"}
    key = "synthetic_reviewer_key"
    api_key = ApiKey(name="Synthetic reviewer escape", key_hash=hash_api_key(key), scopes=["patients.identity_reconciliation.review", "ai.patients.create"], clinic_id=auth_setup["clinic"].id, institution_id=auth_setup["clinic"].institution_id, active=True)
    db.add(api_key); db.commit()
    key_headers = {"X-ASTRA-API-Key": key}
    response = client.get("/api/patient-identity-reconciliations/review/pending", headers=key_headers)
    assert response.status_code == 403
    created = client.post("/api/ai/patients/create", headers=key_headers, json={"first_name": "Ana", "last_name": "Horvat", "date_of_birth": "1987-04-03", "email": "ana.foreign@example.com"})
    assert created.status_code == 202
    status_response = client.get(f"/api/ai/patient-identity-reconciliations/{created.json()['request_id']}", headers=key_headers)
    assert status_response.status_code == 200
    assert "candidate" not in status_response.text.lower()
    assert client.get(f"/api/ai/patient-identity-reconciliations/{created.json()['request_id']}", headers={**key_headers, "X-Clinic-Id": "999999"}).status_code == 403


def test_distinct_rechecks_new_candidate_and_cancel_is_terminal(client, db, auth_setup):
    _foreign_patient(db)
    request_id = _request(client).json()["request_id"]
    reviewer = _reviewer_headers(client, db)
    new_candidate = Patient(first_name="Ana", last_name="Horvat", date_of_birth=date(1987, 4, 3), phone="+385912223333")
    db.add(new_candidate); db.commit()
    before = db.query(Patient).count()
    stale = client.post(f"/api/patient-identity-reconciliations/review/{request_id}/confirm-distinct", headers=reviewer, json={"reason": "Synthetic distinct decision"})
    assert stale.status_code == 409
    assert db.query(Patient).count() == before
    cancelled = client.post(f"/api/patient-identity-reconciliations/{request_id}/cancel", headers=_auth_headers(client), json={"reason": "Requester cancelled synthetic request"})
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert client.post(f"/api/patient-identity-reconciliations/review/{request_id}/approve-link", headers=reviewer, json={"reason": "Late approval", "candidate_patient_id": new_candidate.id}).status_code == 409
