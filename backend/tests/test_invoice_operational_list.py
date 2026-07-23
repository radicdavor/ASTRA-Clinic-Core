from datetime import date
from decimal import Decimal

from app.models.domain import Clinic, ClinicMembership, Invoice, InvoiceLine, Patient, PaymentTransaction
from tests.conftest import login_token


def headers(client, auth_setup, email="admin@test.local"):
    return {
        "Authorization": f"Bearer {login_token(client, email)}",
        "X-Clinic-Id": str(auth_setup["clinic"].id),
    }


def test_operational_invoice_list_is_lightweight_scoped_and_calculates_outstanding(client, db, auth_setup):
    patient = Patient(first_name="Sintetička", last_name="Pacijentica")
    foreign_patient = Patient(first_name="Druga", last_name="Klinika")
    foreign_clinic = Clinic(name="Druga klinika")
    db.add_all([patient, foreign_patient, foreign_clinic])
    db.flush()
    invoice = Invoice(
        patient_id=patient.id,
        clinic_id=auth_setup["clinic"].id,
        invoice_number="ASTRA-SYNTH-1",
        invoice_date=date(2026, 7, 23),
        status="partially_paid",
        payment_status="partially_paid",
        total_amount=Decimal("120"),
    )
    foreign_invoice = Invoice(
        patient_id=foreign_patient.id,
        clinic_id=foreign_clinic.id,
        invoice_number="ASTRA-FOREIGN-1",
        invoice_date=date(2026, 7, 23),
        status="issued",
        payment_status="unpaid",
        total_amount=Decimal("200"),
    )
    db.add_all([invoice, foreign_invoice])
    db.flush()
    db.add_all([
        InvoiceLine(invoice_id=invoice.id, description="Sintetička usluga", quantity=1, unit_price=120, total=120),
        PaymentTransaction(invoice_id=invoice.id, amount=Decimal("40"), method="card"),
    ])
    db.commit()

    response = client.get("/api/invoices/operational-list", headers=headers(client, auth_setup))

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [invoice.id]
    assert payload[0]["patient_name"] == "Sintetička Pacijentica"
    assert Decimal(payload[0]["paid_amount"]) == Decimal("40")
    assert Decimal(payload[0]["outstanding_amount"]) == Decimal("80")
    assert payload[0]["payment_count"] == 1
    assert payload[0]["can_issue"] is True
    assert payload[0]["can_record_payment"] is True
    assert "lines" not in payload[0]
    assert "payments" not in payload[0]


def test_read_only_billing_user_gets_no_mutation_capabilities(client, db, auth_setup):
    patient = Patient(first_name="Samo", last_name="Čitanje")
    db.add(patient)
    db.flush()
    db.add_all([
        Invoice(
            patient_id=patient.id,
            clinic_id=auth_setup["clinic"].id,
            invoice_number="ASTRA-READ-ONLY",
            invoice_date=date(2026, 7, 23),
            status="issued",
            payment_status="unpaid",
            total_amount=Decimal("50"),
        ),
        ClinicMembership(
            user_id=auth_setup["limited"].id,
            clinic_id=auth_setup["clinic"].id,
            created_by_user_id=auth_setup["admin"].id,
        ),
    ])
    db.commit()

    response = client.get(
        "/api/invoices/operational-list",
        headers=headers(client, auth_setup, "limited@test.local"),
    )

    assert response.status_code == 200
    assert response.json()[0]["can_issue"] is False
    assert response.json()[0]["can_record_payment"] is False
