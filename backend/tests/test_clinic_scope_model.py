import pytest
from sqlalchemy.exc import IntegrityError

from app.models.domain import Clinic, ClinicMembership, Patient, PatientClinicAssociation, Permission, Role, User
from app.core.security import hash_password


def test_patient_can_be_associated_with_multiple_clinics(db):
    patient = Patient(first_name="Scope", last_name="Patient")
    clinic_a = Clinic(name="Clinic A")
    clinic_b = Clinic(name="Clinic B")
    db.add_all([patient, clinic_a, clinic_b])
    db.flush()

    db.add_all(
        [
            PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic_a.id),
            PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic_b.id),
        ]
    )
    db.commit()

    associations = {item.clinic_id for item in patient.clinic_associations}
    assert associations == {clinic_a.id, clinic_b.id}


def test_patient_clinic_association_is_unique(db):
    patient = Patient(first_name="Duplicate", last_name="Association")
    clinic = Clinic(name="Unique Clinic")
    db.add_all([patient, clinic])
    db.flush()
    db.add_all(
        [
            PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic.id),
            PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic.id),
        ]
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_user_can_have_multiple_active_clinic_memberships(db):
    permission = Permission(name="patients.read", description="patients.read")
    role = Role(name="scope_role", description="Scope role", permissions=[permission])
    user = User(email="scope@test.local", full_name="Scope User", password_hash=hash_password("secret"), role=role)
    clinic_a = Clinic(name="Membership A")
    clinic_b = Clinic(name="Membership B")
    db.add_all([user, clinic_a, clinic_b])
    db.flush()

    db.add_all(
        [
            ClinicMembership(user_id=user.id, clinic_id=clinic_a.id),
            ClinicMembership(user_id=user.id, clinic_id=clinic_b.id),
        ]
    )
    db.commit()

    assert {membership.clinic_id for membership in user.clinic_memberships} == {clinic_a.id, clinic_b.id}


def test_user_clinic_membership_is_unique(db):
    permission = Permission(name="appointments.read", description="appointments.read")
    role = Role(name="membership_unique_role", description="Membership role", permissions=[permission])
    user = User(email="membership@test.local", full_name="Membership User", password_hash=hash_password("secret"), role=role)
    clinic = Clinic(name="Membership Unique Clinic")
    db.add_all([user, clinic])
    db.flush()
    db.add_all(
        [
            ClinicMembership(user_id=user.id, clinic_id=clinic.id),
            ClinicMembership(user_id=user.id, clinic_id=clinic.id),
        ]
    )

    with pytest.raises(IntegrityError):
        db.commit()
