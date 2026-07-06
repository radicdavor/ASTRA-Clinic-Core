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
    assert created.json()["review_status"] == "draft"
    assert created.json()["physician_reviewed"] is False
    document_id = created.json()["id"]

    summary_before = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary_before.status_code == 200
    assert summary_before.json()["generated_from_reviewed_documents"] == 0
    assert summary_before.json()["awaiting_review_count"] == 0

    extracted = client.post(f"/api/clinical-documents/{document_id}/extract", headers=headers)
    assert extracted.status_code == 200
    assert extracted.json()["physician_reviewed"] is False
    assert extracted.json()["review_status"] == "needs_physician_review"
    assert extracted.json()["key_findings"]

    summary_after_extraction = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary_after_extraction.status_code == 200
    assert summary_after_extraction.json()["generated_from_reviewed_documents"] == 0
    assert summary_after_extraction.json()["awaiting_review_count"] == 1

    edited = client.patch(
        f"/api/clinical-documents/{document_id}",
        headers=headers,
        json={
            "ai_summary": "Uredeni sazetak prije potvrde.",
            "key_findings": ["GERB/refluks naveden u dokumentu"],
            "recommendations": ["Kontrola nakon nalaza"],
        },
    )
    assert edited.status_code == 200
    assert edited.json()["physician_reviewed"] is False
    assert edited.json()["review_status"] == "needs_physician_review"

    reviewed = client.post(f"/api/clinical-documents/{document_id}/review", headers=headers)
    assert reviewed.status_code == 200
    assert reviewed.json()["physician_reviewed"] is True
    assert reviewed.json()["review_status"] == "reviewed"

    summary_after = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary_after.status_code == 200
    body = summary_after.json()
    assert body["generated_from_reviewed_documents"] == 1
    assert body["known_problems"] or body["completed_procedures"]
    first_item = (body["known_problems"] or body["completed_procedures"])[0]
    assert first_item["sources"][0]["document_id"] == document_id
    for category in ["known_problems", "completed_procedures", "pathology", "laboratory", "imaging", "current_therapy", "open_questions", "latest_recommendations"]:
        for item in body[category]:
            assert item["sources"]


def test_reject_summary_removes_ai_items_from_patient_summary(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    rejected = client.post(f"/api/clinical-documents/{doc.id}/reject-summary", headers=headers)
    assert rejected.status_code == 200
    assert rejected.json()["physician_reviewed"] is False
    assert rejected.json()["key_findings"] == []
    assert rejected.json()["review_status"] == "rejected"

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


def test_patient_summary_merges_duplicate_items_and_sources(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc_one = clinical_document(db, p, physician_reviewed=True)
    doc_two = clinical_document(db, p, physician_reviewed=True)
    doc_two.key_findings = ["GERB/refluks naveden u dokumentu"]
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    items = summary.json()["known_problems"] + summary.json()["completed_procedures"]
    matching = [item for item in items if item["text"] == "GERB/refluks naveden u dokumentu"]
    assert len(matching) == 1
    assert {source["document_id"] for source in matching[0]["sources"]} == {doc_one.id, doc_two.id}


def test_patient_summary_requires_reviewed_status_and_compatibility_flag(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    inconsistent = clinical_document(db, p, physician_reviewed=True)
    inconsistent.review_status = "needs_physician_review"
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["generated_from_reviewed_documents"] == 0
    assert summary.json()["known_problems"] == []


def test_updating_raw_or_extracted_fields_resets_review_metadata(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)

    updated = client.patch(
        f"/api/clinical-documents/{doc.id}",
        headers=headers,
        json={"raw_text": "Novi tekst dokumenta koji zahtijeva ponovni pregled."},
    )

    assert updated.status_code == 200
    body = updated.json()
    assert body["review_status"] == "needs_physician_review"
    assert body["physician_reviewed"] is False
    assert body["reviewed_by"] is None
    assert body["reviewed_at"] is None


def test_readiness_deep_links_to_unreviewed_documents(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    clinical_document(db, p, physician_reviewed=False)

    response = client.get("/api/readiness", headers=headers)
    assert response.status_code == 200
    check = next(item for item in response.json()["checks"] if item["key"] == "clinical_documents_review")
    assert check["target_path"] == "/clinical-documents?review_status=needs_physician_review"
    assert check["target_label"] == "Pregledaj dokumente"


def test_generate_edit_and_review_patient_clinical_summary(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)

    draft = client.post(f"/api/patients/{p.id}/clinical-summary/generate-draft", headers=headers)
    assert draft.status_code == 200
    draft_body = draft.json()
    assert draft_body["status"] == "needs_review"
    assert doc.id in draft_body["source_document_ids"]

    edited = client.patch(
        f"/api/patients/{p.id}/clinical-summary",
        headers=headers,
        json={"summary_text": "Lijecnicki uredjen sazetak.", "open_items": ["Rucno provjeriti izvore"]},
    )
    assert edited.status_code == 200
    assert edited.json()["summary_text"] == "Lijecnicki uredjen sazetak."
    assert edited.json()["status"] == "needs_review"

    reviewed = client.post(f"/api/patients/{p.id}/clinical-summary/review", headers=headers)
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "reviewed"
    assert reviewed.json()["reviewed_at"]

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["reviewed_summary"]["summary_text"] == "Lijecnicki uredjen sazetak."


def test_readiness_detects_stale_patient_summary(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    clinical_document(db, p, physician_reviewed=True)

    response = client.get("/api/readiness", headers=headers)
    assert response.status_code == 200
    check = next(item for item in response.json()["checks"] if item["key"] == "patient_summary_stale")
    assert check["status"] == "warning"
    assert check["target_path"] == "/patients"
