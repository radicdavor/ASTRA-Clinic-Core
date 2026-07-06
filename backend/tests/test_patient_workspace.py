from datetime import date, time
from decimal import Decimal

from app.models.domain import Appointment, Invoice, Patient, Provider, Room, Service
from tests.conftest import login_token


def seed_patient_workspace(db):
    patient = Patient(first_name="Ana", last_name="Horvat")
    other = Patient(first_name="Ivo", last_name="Ivic")
    provider = Provider(full_name="Dr. Demo", active=True)
    room = Room(name="Soba 1", active=True)
    service = Service(name="Pregled", duration_minutes=30, price=Decimal("50.00"), active=True)
    db.add_all([patient, other, provider, room, service])
    db.flush()
    appointment = Appointment(patient_id=patient.id, provider_id=provider.id, room_id=room.id, service_id=service.id, date=date(2026, 7, 5), start_time=time(9, 0), end_time=time(9, 30), duration_minutes=30)
    other_appointment = Appointment(patient_id=other.id, provider_id=provider.id, room_id=room.id, service_id=service.id, date=date(2026, 7, 6), start_time=time(9, 0), end_time=time(9, 30), duration_minutes=30)
    invoice = Invoice(patient_id=patient.id, invoice_number="ASTRA-1", status="issued", total_amount=Decimal("50.00"), payment_status="unpaid")
    other_invoice = Invoice(patient_id=other.id, invoice_number="ASTRA-2", status="issued", total_amount=Decimal("20.00"), payment_status="unpaid")
    db.add_all([appointment, other_appointment, invoice, other_invoice])
    db.commit()
    return patient


def test_patient_appointments_returns_only_that_patient(client, db, auth_setup):
    patient = seed_patient_workspace(db)
    token = login_token(client, "admin@test.local")

    response = client.get(f"/api/patients/{patient.id}/appointments", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["patient_id"] == patient.id


def test_patient_invoices_returns_only_that_patient(client, db, auth_setup):
    patient = seed_patient_workspace(db)
    token = login_token(client, "admin@test.local")

    response = client.get(f"/api/patients/{patient.id}/invoices", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["patient_id"] == patient.id


def test_patient_appointments_require_permission(client, db, auth_setup):
    patient = seed_patient_workspace(db)
    token = login_token(client, "limited@test.local")

    response = client.get(f"/api/patients/{patient.id}/appointments", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
