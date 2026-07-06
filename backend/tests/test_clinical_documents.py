from tests.conftest import login_token
from tests.factories import appointment, clinical_document, patient


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def test_create_extract_review_document_updates_patient_summary(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    created = client.post(
        "/api/clinical-documents",
        headers=headers,
        json={
            "patient_id": p.id,
            "source_type": "external",
            "document_type": "gastroscopy",
            "origin": "KBC Zagreb",
            "document_date": "2026-07-05",
            "title": "Vanjska gastroskopija",
            "raw_text": "Gastroskopija pokazuje GERB/refluks. H. pylori negativan. Esomeprazol terapija.",
        },
    )
    assert created.status_code == 200
    document_id = created.json()["id"]

    summary_before = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary_before.status_code == 200
    assert summary_before.json()["generated_from_reviewed_documents"] == 0
    assert summary_before.json()["awaiting_review_count"] == 1

    extracted = client.post(f"/api/clinical-documents/{document_id}/extract", headers=headers)
    assert extracted.status_code == 200
    assert extracted.json()["physician_reviewed"] is False
    assert extracted.json()["key_findings"]

    reviewed = client.post(f"/api/clinical-documents/{document_id}/review", headers=headers)
    assert reviewed.status_code == 200
    assert reviewed.json()["physician_reviewed"] is True

    summary_after = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary_after.status_code == 200
    body = summary_after.json()
    assert body["generated_from_reviewed_documents"] == 1
    assert body["known_problems"] or body["completed_procedures"]
    first_item = (body["known_problems"] or body["completed_procedures"])[0]
    assert first_item["sources"][0]["document_id"] == document_id


def test_reject_summary_removes_ai_items_from_patient_summary(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    rejected = client.post(f"/api/clinical-documents/{doc.id}/reject-summary", headers=headers)
    assert rejected.status_code == 200
    assert rejected.json()["physician_reviewed"] is False
    assert rejected.json()["key_findings"] == []

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["generated_from_reviewed_documents"] == 0


def test_document_appointment_must_belong_to_same_patient(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db, "Doc", "Patient")
    other = patient(db, "Other", "Patient")
    appt = appointment(db, patient_obj=other)
    response = client.post(
        "/api/clinical-documents",
        headers=headers,
        json={
            "patient_id": p.id,
            "appointment_id": appt.id,
            "source_type": "internal",
            "document_type": "consultation",
            "title": "Krivi termin",
        },
    )
    assert response.status_code == 422


def test_limited_user_cannot_read_clinical_documents(client, db, auth_setup):
    token = login_token(client, "limited@test.local")
    response = client.get("/api/clinical-documents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
