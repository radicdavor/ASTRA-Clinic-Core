from datetime import datetime

from app.models.domain import AuditLog, PatientClinicalSummaryRecord
from tests.conftest import login_token
from tests.factories import appointment, clinical_document, patient


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


KNOWLEDGE_CATEGORIES = [
    "known_problems",
    "completed_procedures",
    "pathology",
    "laboratory",
    "imaging",
    "current_therapy",
    "open_questions",
    "latest_recommendations",
]


def all_knowledge_items(summary_body):
    return [item for category in KNOWLEDGE_CATEGORIES for item in summary_body[category]]


def assert_no_official_knowledge(summary_body):
    assert summary_body["generated_from_reviewed_documents"] == 0
    assert all_knowledge_items(summary_body) == []


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
    assert created.json()["ai_extraction_status"] == "not_run"
    assert created.json()["ai_extraction_generated_at"] is None
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
    assert extracted.json()["ai_extraction_status"] == "generated"
    assert extracted.json()["ai_extraction_generated_at"]
    assert extracted.json()["ai_extraction_updated_at"]
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
    assert edited.json()["ai_extraction_status"] == "edited"
    assert edited.json()["ai_extraction_updated_at"]

    reviewed = client.post(f"/api/clinical-documents/{document_id}/review", headers=headers)
    assert reviewed.status_code == 200
    assert reviewed.json()["physician_reviewed"] is True
    assert reviewed.json()["review_status"] == "reviewed"
    assert reviewed.json()["ai_extraction_status"] == "accepted"

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
    raw_text = doc.raw_text
    rejected = client.post(f"/api/clinical-documents/{doc.id}/reject-summary", headers=headers)
    assert rejected.status_code == 200
    assert rejected.json()["physician_reviewed"] is False
    assert rejected.json()["key_findings"] == []
    assert rejected.json()["raw_text"] == raw_text
    assert rejected.json()["review_status"] == "draft"
    assert rejected.json()["ai_extraction_status"] == "rejected"
    assert rejected.json()["ai_extraction_updated_at"]

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["generated_from_reviewed_documents"] == 0


def test_rejected_ai_extraction_can_be_generated_again(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    rejected = client.post(f"/api/clinical-documents/{doc.id}/reject-summary", headers=headers)
    assert rejected.status_code == 200
    assert rejected.json()["ai_extraction_status"] == "rejected"

    extracted = client.post(f"/api/clinical-documents/{doc.id}/extract", headers=headers)
    assert extracted.status_code == 200
    assert extracted.json()["review_status"] == "needs_physician_review"
    assert extracted.json()["ai_extraction_status"] == "generated"
    assert extracted.json()["key_findings"]


def test_rejected_ai_extraction_requires_review_before_official_knowledge(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    rejected = client.post(f"/api/clinical-documents/{doc.id}/reject-summary", headers=headers)
    assert rejected.status_code == 200
    assert rejected.json()["review_status"] == "draft"

    edited = client.patch(
        f"/api/clinical-documents/{doc.id}",
        headers=headers,
        json={"key_findings": ["Rucno strukturirana tvrdnja iz izvora"]},
    )
    assert edited.status_code == 200
    assert edited.json()["review_status"] == "needs_physician_review"
    assert edited.json()["ai_extraction_status"] == "edited"

    summary_before_review = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary_before_review.status_code == 200
    assert summary_before_review.json()["generated_from_reviewed_documents"] == 0

    reviewed = client.post(f"/api/clinical-documents/{doc.id}/review", headers=headers)
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "reviewed"

    summary_after_review = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary_after_review.status_code == 200
    body = summary_after_review.json()
    assert body["generated_from_reviewed_documents"] == 1
    assert any(item["text"] == "Rucno strukturirana tvrdnja iz izvora" for item in all_knowledge_items(body))


def test_clinical_document_detail_exposes_source_ai_and_review_lifecycle(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    created = client.post(
        "/api/clinical-documents",
        headers=headers,
        json={
            "patient_id": p.id,
            "source_type": "external",
            "document_type": "colonoscopy",
            "origin": "Vanjska ustanova",
            "document_date": "2026-07-05",
            "title": "Vanjska kolonoskopija",
            "raw_text": "Kolonoskopija: polip odstranjen. Ceka se PHD nalaz.",
        },
    )
    assert created.status_code == 200
    document_id = created.json()["id"]

    detail_before = client.get(f"/api/clinical-documents/{document_id}", headers=headers)
    assert detail_before.status_code == 200
    assert detail_before.json()["raw_text"] == "Kolonoskopija: polip odstranjen. Ceka se PHD nalaz."
    assert detail_before.json()["review_status"] == "draft"
    assert detail_before.json()["ai_extraction_status"] == "not_run"
    assert detail_before.json()["physician_reviewed"] is False

    extracted = client.post(f"/api/clinical-documents/{document_id}/extract", headers=headers)
    assert extracted.status_code == 200
    detail_after_extraction = client.get(f"/api/clinical-documents/{document_id}", headers=headers)
    assert detail_after_extraction.status_code == 200
    assert detail_after_extraction.json()["review_status"] == "needs_physician_review"
    assert detail_after_extraction.json()["ai_extraction_status"] == "generated"
    assert detail_after_extraction.json()["key_findings"]

    rejected = client.post(f"/api/clinical-documents/{document_id}/reject-summary", headers=headers)
    assert rejected.status_code == 200
    detail_after_reject = client.get(f"/api/clinical-documents/{document_id}", headers=headers)
    assert detail_after_reject.status_code == 200
    assert detail_after_reject.json()["raw_text"] == "Kolonoskopija: polip odstranjen. Ceka se PHD nalaz."
    assert detail_after_reject.json()["key_findings"] == []
    assert detail_after_reject.json()["recommendations"] == []
    assert detail_after_reject.json()["review_status"] == "draft"
    assert detail_after_reject.json()["ai_extraction_status"] == "rejected"
    assert detail_after_reject.json()["physician_reviewed"] is False

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert_no_official_knowledge(summary.json())


def test_rejected_and_superseded_document_details_remain_visible_but_not_official(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    rejected = clinical_document(db, p, physician_reviewed=False)
    rejected.review_status = "rejected"
    rejected.ai_extraction_status = "rejected"
    rejected.key_findings = ["Odbijeni nalaz ne smije biti sluzben"]
    superseded = clinical_document(db, p, physician_reviewed=True)
    superseded.review_status = "superseded"
    superseded.ai_extraction_status = "superseded"
    superseded.key_findings = ["Zamijenjeni nalaz ne smije biti sluzben"]
    db.commit()

    rejected_detail = client.get(f"/api/clinical-documents/{rejected.id}", headers=headers)
    superseded_detail = client.get(f"/api/clinical-documents/{superseded.id}", headers=headers)
    assert rejected_detail.status_code == 200
    assert superseded_detail.status_code == 200
    assert rejected_detail.json()["review_status"] == "rejected"
    assert rejected_detail.json()["key_findings"] == ["Odbijeni nalaz ne smije biti sluzben"]
    assert superseded_detail.json()["review_status"] == "superseded"
    assert superseded_detail.json()["key_findings"] == ["Zamijenjeni nalaz ne smije biti sluzben"]

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert_no_official_knowledge(summary.json())


def test_clinical_document_evidence_timeline_returns_classified_document_events(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    created = client.post(
        "/api/clinical-documents",
        headers=headers,
        json={
            "patient_id": p.id,
            "source_type": "external",
            "document_type": "gastroscopy",
            "origin": "Vanjska ustanova",
            "document_date": "2026-07-05",
            "title": "Evidence timeline dokument",
            "raw_text": "GERB refluks. H. pylori negativan.",
        },
    )
    assert created.status_code == 200
    document_id = created.json()["id"]

    extracted = client.post(f"/api/clinical-documents/{document_id}/extract", headers=headers)
    assert extracted.status_code == 200
    reviewed = client.post(f"/api/clinical-documents/{document_id}/review", headers=headers)
    assert reviewed.status_code == 200
    rejected = client.post(f"/api/clinical-documents/{document_id}/reject-summary", headers=headers)
    assert rejected.status_code == 200
    db.add(AuditLog(action="update", entity_type="Patient", entity_id=p.id, summary="Ne pripada timelineu dokumenta"))
    db.commit()

    response = client.get(f"/api/clinical-documents/{document_id}/evidence-timeline", headers=headers)
    assert response.status_code == 200
    body = response.json()
    actions = [item["action"] for item in body]
    assert actions == ["ai_document_summary_rejected", "clinical_document_reviewed", "ai_document_extracted", "create"]
    assert [item["id"] for item in body] == sorted([item["id"] for item in body], reverse=True)
    assert all(item["object_type"] == "ClinicalDocument" for item in body)
    assert all(item["object_id"] == document_id for item in body)
    assert "update" not in actions

    extracted_item = next(item for item in body if item["action"] == "ai_document_extracted")
    assert extracted_item["clinical_event_category"] == "ai_extraction"
    assert extracted_item["clinical_event_label"] == "AI prijedlog generiran"
    assert extracted_item["knowledge_impact"] == "no_official_knowledge_impact"

    reviewed_item = next(item for item in body if item["action"] == "clinical_document_reviewed")
    assert reviewed_item["clinical_event_category"] == "physician_review"
    assert reviewed_item["clinical_event_label"] == "Lijecnicki pregledano"
    assert reviewed_item["knowledge_impact"] == "may_enable_official_knowledge"


def test_clinical_document_evidence_timeline_requires_existing_document(client, auth_setup):
    headers = auth_headers(client)
    response = client.get("/api/clinical-documents/999/evidence-timeline", headers=headers)
    assert response.status_code == 404


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


def test_unreviewed_generated_ai_extraction_is_not_official_knowledge(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=False)
    doc.ai_extraction_status = "generated"
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert_no_official_knowledge(summary.json())


def test_edited_unreviewed_ai_extraction_is_not_official_knowledge(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=False)
    doc.ai_extraction_status = "edited"
    doc.key_findings = ["GERB/refluks naveden u dokumentu"]
    doc.recommendations = ["Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled"]
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert_no_official_knowledge(summary.json())


def test_rejected_document_is_not_official_knowledge(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=False)
    doc.review_status = "rejected"
    doc.ai_extraction_status = "rejected"
    doc.physician_reviewed = False
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert_no_official_knowledge(summary.json())


def test_superseded_document_does_not_contribute_if_status_supported(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    doc.review_status = "superseded"
    doc.ai_extraction_status = "superseded"
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert_no_official_knowledge(summary.json())


def test_reviewed_document_with_accepted_ai_extraction_is_official_knowledge(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    doc.ai_extraction_status = "accepted"
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["generated_from_reviewed_documents"] == 1
    assert any(source["document_id"] == doc.id for item in all_knowledge_items(body) for source in item["sources"])


def test_reviewed_manual_document_without_ai_extraction_can_be_official_knowledge(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    doc.ai_extraction_status = "not_run"
    doc.ai_summary = None
    doc.key_findings = ["Rucno unesena pregledana klinicka tvrdnja"]
    doc.recommendations = []
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["generated_from_reviewed_documents"] == 1
    matching = [item for item in all_knowledge_items(body) if item["text"] == "Rucno unesena pregledana klinicka tvrdnja"]
    assert len(matching) == 1
    assert matching[0]["sources"][0]["document_id"] == doc.id


def test_summary_record_alone_does_not_create_official_knowledge(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    record = PatientClinicalSummaryRecord(
        patient_id=p.id,
        summary_text="Pregledani sazetak bez source dokumenta.",
        known_conditions=["GERB bez source dokumenta"],
        key_findings=["Nalaz bez source dokumenta"],
        open_items=["Otvoreno pitanje bez source dokumenta"],
        risks=[],
        last_recommendations=["Preporuka bez source dokumenta"],
        source_document_ids=[],
        status="reviewed",
        generated_by="physician",
        reviewed_by=1,
        reviewed_at=datetime(2026, 7, 6),
    )
    db.add(record)
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["reviewed_summary"] is None
    assert_no_official_knowledge(body)


def test_official_knowledge_items_always_have_sources(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    clinical_document(db, p, physician_reviewed=True)

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    for item in all_knowledge_items(summary.json()):
        assert item["sources"]
        for source in item["sources"]:
            assert source["document_id"]
            assert source["title"]
            assert source["document_type"]
            assert source["source_type"]
            assert "origin" in source
            assert "document_date" in source


def test_open_questions_require_reviewed_sources(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    unreviewed = clinical_document(db, p, physician_reviewed=False)
    unreviewed.recommendations = ["Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled"]
    reviewed = clinical_document(db, p, physician_reviewed=True)
    reviewed.recommendations = ["Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled"]
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    open_questions = summary.json()["open_questions"]
    assert len(open_questions) == 1
    assert {source["document_id"] for source in open_questions[0]["sources"]} == {reviewed.id}
    assert open_questions[0]["display_kind"] == "open_question"
    assert open_questions[0]["severity"] == "warning"
    assert open_questions[0]["requires_attention"] is True


def test_open_question_recommendation_keywords_are_classified(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    keywords = ["ceka nalaz patologije", "čeka nalaz patologije", "pending patologija", "otvoreno pitanje kontrole"]
    for text in keywords:
        doc = clinical_document(db, p, physician_reviewed=True)
        doc.key_findings = []
        doc.recommendations = [text]
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    open_question_texts = [item["text"] for item in body["open_questions"]]
    assert set(open_question_texts) == set(keywords)
    assert body["latest_recommendations"] == []


def test_reviewed_recommendation_without_unresolved_language_is_latest_recommendation(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    doc.key_findings = []
    doc.recommendations = ["Kontrola prema odluci lijecnika"]
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["open_questions"] == []
    assert body["latest_recommendations"][0]["text"] == "Kontrola prema odluci lijecnika"
    assert body["latest_recommendations"][0]["sources"][0]["document_id"] == doc.id
    assert body["latest_recommendations"][0]["display_kind"] is None
    assert body["latest_recommendations"][0]["severity"] is None
    assert body["latest_recommendations"][0]["requires_attention"] is False


def test_reviewed_raw_text_with_pending_language_creates_generic_open_question(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    first = clinical_document(db, p, physician_reviewed=True)
    first.key_findings = []
    first.recommendations = []
    first.raw_text = "Čeka se nalaz patologije."
    second = clinical_document(db, p, physician_reviewed=True)
    second.key_findings = []
    second.recommendations = []
    second.raw_text = "Pathology pending."
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    open_questions = summary.json()["open_questions"]
    assert len(open_questions) == 1
    assert open_questions[0]["text"] == "Dokument sadrzi otvoreno pitanje koje zahtijeva pregled."
    assert {source["document_id"] for source in open_questions[0]["sources"]} == {first.id, second.id}
    assert open_questions[0]["display_kind"] == "open_question"
    assert open_questions[0]["severity"] == "warning"
    assert open_questions[0]["requires_attention"] is True


def test_rejected_and_superseded_documents_never_create_open_questions(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    rejected = clinical_document(db, p, physician_reviewed=False)
    rejected.review_status = "rejected"
    rejected.recommendations = ["Postoji otvoreno pitanje koje ceka pregled"]
    superseded = clinical_document(db, p, physician_reviewed=True)
    superseded.review_status = "superseded"
    superseded.recommendations = ["Postoji otvoreno pitanje koje ceka pregled"]
    draft = clinical_document(db, p, physician_reviewed=False)
    draft.review_status = "draft"
    draft.recommendations = ["Postoji otvoreno pitanje koje ceka pregled"]
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["open_questions"] == []


def test_open_questions_remain_separate_from_known_problems_and_recommendations(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    doc.key_findings = ["GERB/refluks naveden u dokumentu"]
    doc.recommendations = ["Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled", "Kontrola prema odluci lijecnika"]
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert [item["text"] for item in body["open_questions"]] == ["Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled"]
    assert [item["text"] for item in body["latest_recommendations"]] == ["Kontrola prema odluci lijecnika"]
    assert all(item["text"] != "Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled" for item in body["known_problems"])


def test_review_without_ai_extraction_keeps_ai_status_not_run(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    created = client.post(
        "/api/clinical-documents",
        headers=headers,
        json={
            "patient_id": p.id,
            "source_type": "external",
            "document_type": "other",
            "title": "Rucno pregledani izvor bez AI ekstrakcije",
            "raw_text": "Rucni izvor bez AI ekstrakcije.",
        },
    )
    assert created.status_code == 200
    document_id = created.json()["id"]

    reviewed = client.post(f"/api/clinical-documents/{document_id}/review", headers=headers)
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "reviewed"
    assert reviewed.json()["physician_reviewed"] is True
    assert reviewed.json()["ai_extraction_status"] == "not_run"
    assert reviewed.json()["key_findings"] is None


def test_official_knowledge_does_not_require_accepted_ai_status_for_manual_content(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    doc.ai_extraction_status = "not_run"
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["generated_from_reviewed_documents"] == 1
    assert summary.json()["known_problems"] or summary.json()["completed_procedures"]


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
    assert body["ai_extraction_status"] == "edited"
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


def test_readiness_counts_generated_and_edited_extraction_awaiting_review(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    clinical_document(db, p, physician_reviewed=False)

    response = client.get("/api/readiness", headers=headers)
    assert response.status_code == 200
    check = next(item for item in response.json()["checks"] if item["key"] == "clinical_documents_review")
    assert check["count"] == 1


def test_readiness_counts_needs_physician_review_documents_only(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    clinical_document(db, p, physician_reviewed=False)
    reviewed = clinical_document(db, p, physician_reviewed=True)
    rejected = clinical_document(db, p, physician_reviewed=False)
    rejected.review_status = "rejected"
    rejected.ai_extraction_status = "rejected"
    superseded = clinical_document(db, p, physician_reviewed=False)
    superseded.review_status = "superseded"
    superseded.ai_extraction_status = "superseded"
    draft = clinical_document(db, p, physician_reviewed=False)
    draft.review_status = "draft"
    draft.ai_extraction_status = "not_run"
    draft.key_findings = None
    draft.recommendations = None
    extracted = clinical_document(db, p, physician_reviewed=False)
    extracted.review_status = "extracted"
    db.commit()

    response = client.get("/api/readiness", headers=headers)
    assert response.status_code == 200
    check = next(item for item in response.json()["checks"] if item["key"] == "clinical_documents_review")
    assert check["count"] == 2
    assert reviewed.review_status == "reviewed"
    assert rejected.review_status == "rejected"
    assert superseded.review_status == "superseded"
    assert draft.review_status == "draft"


def test_generate_edit_and_review_patient_clinical_summary(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)

    draft = client.post(f"/api/patients/{p.id}/clinical-summary/generate-draft", headers=headers)
    assert draft.status_code == 200
    draft_body = draft.json()
    assert draft_body["status"] == "draft_ai"
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
    assert summary.json()["reviewed_summary_is_stale"] is False
    assert summary.json()["summary_warning"] is None


def test_patient_summary_draft_uses_only_reviewed_documents(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    reviewed = clinical_document(db, p, physician_reviewed=True)
    unreviewed = clinical_document(db, p, physician_reviewed=False)
    unreviewed.key_findings = ["Nepregledana tvrdnja ne smije u draft"]
    db.commit()

    draft = client.post(f"/api/patients/{p.id}/clinical-summary/generate-draft", headers=headers)
    assert draft.status_code == 200
    body = draft.json()
    assert body["status"] == "draft_ai"
    assert body["source_document_ids"] == [reviewed.id]
    assert "Nepregledana tvrdnja ne smije u draft" not in body["known_conditions"]
    assert "Nepregledana tvrdnja ne smije u draft" not in body["key_findings"]


def test_patient_summary_draft_excludes_rejected_and_superseded_documents(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    reviewed = clinical_document(db, p, physician_reviewed=True)
    draft_document = clinical_document(db, p, physician_reviewed=False)
    draft_document.review_status = "draft"
    draft_document.key_findings = ["Draft tvrdnja"]
    needs_review = clinical_document(db, p, physician_reviewed=False)
    needs_review.review_status = "needs_physician_review"
    needs_review.key_findings = ["Tvrdnja koja ceka pregled"]
    rejected = clinical_document(db, p, physician_reviewed=False)
    rejected.review_status = "rejected"
    rejected.key_findings = ["Odbijena tvrdnja"]
    superseded = clinical_document(db, p, physician_reviewed=True)
    superseded.review_status = "superseded"
    superseded.key_findings = ["Zamijenjena tvrdnja"]
    db.commit()

    draft = client.post(f"/api/patients/{p.id}/clinical-summary/generate-draft", headers=headers)
    assert draft.status_code == 200
    body = draft.json()
    assert body["source_document_ids"] == [reviewed.id]
    assert "Draft tvrdnja" not in body["known_conditions"] + body["key_findings"]
    assert "Tvrdnja koja ceka pregled" not in body["known_conditions"] + body["key_findings"]
    assert "Odbijena tvrdnja" not in body["known_conditions"] + body["key_findings"]
    assert "Zamijenjena tvrdnja" not in body["known_conditions"] + body["key_findings"]


def test_review_summary_sets_review_metadata(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    draft = client.post(f"/api/patients/{p.id}/clinical-summary/generate-draft", headers=headers)
    assert draft.status_code == 200

    reviewed = client.post(f"/api/patients/{p.id}/clinical-summary/review", headers=headers)
    assert reviewed.status_code == 200
    body = reviewed.json()
    assert body["status"] == "reviewed"
    assert body["reviewed_by"]
    assert body["reviewed_at"]
    assert body["source_document_ids"] == [doc.id]


def test_reviewed_summary_is_view_not_source_of_truth(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    record = PatientClinicalSummaryRecord(
        patient_id=p.id,
        summary_text="Pregledani sazetak bez izvora.",
        known_conditions=["Sazetak nije izvor istine"],
        key_findings=[],
        open_items=[],
        risks=[],
        last_recommendations=[],
        source_document_ids=[],
        status="reviewed",
        generated_by="physician",
        reviewed_by=1,
        reviewed_at=datetime(2026, 7, 6),
    )
    db.add(record)
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["reviewed_summary"] is None
    assert_no_official_knowledge(body)


def test_reviewed_summary_stale_when_new_reviewed_document_added(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    old_doc = clinical_document(db, p, physician_reviewed=True)
    old_doc.updated_at = datetime(2026, 7, 1, 9, 0)
    db.commit()
    draft = client.post(f"/api/patients/{p.id}/clinical-summary/generate-draft", headers=headers)
    assert draft.status_code == 200
    reviewed = client.post(f"/api/patients/{p.id}/clinical-summary/review", headers=headers)
    assert reviewed.status_code == 200
    record = db.get(PatientClinicalSummaryRecord, reviewed.json()["id"])
    record.updated_at = datetime(2026, 7, 2, 9, 0)
    new_doc = clinical_document(db, p, physician_reviewed=True)
    new_doc.updated_at = datetime(2026, 7, 3, 9, 0)
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["reviewed_summary_is_stale"] is True
    assert body["draft_summary_is_stale"] is False
    assert body["latest_reviewed_document_updated_at"]
    assert body["reviewed_summary_updated_at"]
    assert body["summary_warning"] == "Pregledani sazetak je zastario jer postoje noviji pregledani dokumenti."


def test_draft_summary_stale_when_new_reviewed_document_added(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    old_doc = clinical_document(db, p, physician_reviewed=True)
    old_doc.updated_at = datetime(2026, 7, 1, 9, 0)
    db.commit()
    draft = client.post(f"/api/patients/{p.id}/clinical-summary/generate-draft", headers=headers)
    assert draft.status_code == 200
    record = db.get(PatientClinicalSummaryRecord, draft.json()["id"])
    record.updated_at = datetime(2026, 7, 2, 9, 0)
    new_doc = clinical_document(db, p, physician_reviewed=True)
    new_doc.updated_at = datetime(2026, 7, 3, 9, 0)
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["reviewed_summary_is_stale"] is False
    assert body["draft_summary_is_stale"] is True
    assert body["summary_warning"] == "AI draft sazetka je zastario jer postoje noviji pregledani dokumenti."


def test_readiness_does_not_warn_when_reviewed_summary_current(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    doc = clinical_document(db, p, physician_reviewed=True)
    doc.updated_at = datetime(2026, 7, 1, 9, 0)
    db.commit()
    draft = client.post(f"/api/patients/{p.id}/clinical-summary/generate-draft", headers=headers)
    assert draft.status_code == 200
    reviewed = client.post(f"/api/patients/{p.id}/clinical-summary/review", headers=headers)
    assert reviewed.status_code == 200
    record = db.get(PatientClinicalSummaryRecord, reviewed.json()["id"])
    record.updated_at = datetime(2026, 7, 2, 9, 0)
    db.commit()

    response = client.get("/api/readiness", headers=headers)
    assert response.status_code == 200
    check = next(item for item in response.json()["checks"] if item["key"] == "patient_summary_stale")
    assert check["status"] == "ok"
    assert check["count"] == 0


def test_review_stale_draft_is_blocked(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    old_doc = clinical_document(db, p, physician_reviewed=True)
    old_doc.updated_at = datetime(2026, 7, 1, 9, 0)
    db.commit()
    draft = client.post(f"/api/patients/{p.id}/clinical-summary/generate-draft", headers=headers)
    assert draft.status_code == 200
    record = db.get(PatientClinicalSummaryRecord, draft.json()["id"])
    record.updated_at = datetime(2026, 7, 2, 9, 0)
    new_doc = clinical_document(db, p, physician_reviewed=True)
    new_doc.updated_at = datetime(2026, 7, 3, 9, 0)
    db.commit()

    reviewed = client.post(f"/api/patients/{p.id}/clinical-summary/review", headers=headers)
    assert reviewed.status_code == 409
    assert reviewed.json()["detail"] == "Sazetak je zastario jer postoje noviji pregledani dokumenti. Generirajte novi draft prije potvrde."


def test_latest_reviewed_summary_selection_is_deterministic(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    source = clinical_document(db, p, physician_reviewed=True)
    older = PatientClinicalSummaryRecord(patient_id=p.id, summary_text="Stariji sazetak", source_document_ids=[source.id], status="reviewed", generated_by="physician", reviewed_by=1, reviewed_at=datetime(2026, 7, 1))
    newer = PatientClinicalSummaryRecord(patient_id=p.id, summary_text="Noviji sazetak", source_document_ids=[source.id], status="reviewed", generated_by="physician", reviewed_by=1, reviewed_at=datetime(2026, 7, 2))
    db.add_all([older, newer])
    db.flush()
    older.updated_at = datetime(2026, 7, 1, 9, 0)
    newer.updated_at = datetime(2026, 7, 2, 9, 0)
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["reviewed_summary"]["id"] == newer.id
    assert summary.json()["reviewed_summary"]["summary_text"] == "Noviji sazetak"


def test_latest_reviewed_summary_selection_uses_id_when_timestamp_matches(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    source = clinical_document(db, p, physician_reviewed=True)
    first = PatientClinicalSummaryRecord(patient_id=p.id, summary_text="Prvi sazetak", source_document_ids=[source.id], status="reviewed", generated_by="physician", reviewed_by=1, reviewed_at=datetime(2026, 7, 1))
    second = PatientClinicalSummaryRecord(patient_id=p.id, summary_text="Drugi sazetak", source_document_ids=[source.id], status="reviewed", generated_by="physician", reviewed_by=1, reviewed_at=datetime(2026, 7, 1))
    db.add_all([first, second])
    db.flush()
    same_time = datetime(2026, 7, 2, 9, 0)
    first.updated_at = same_time
    second.updated_at = same_time
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["reviewed_summary"]["id"] == second.id
    assert summary.json()["reviewed_summary"]["summary_text"] == "Drugi sazetak"


def test_rejected_summary_not_selected_as_reviewed_summary_if_rejection_exists(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    rejected = PatientClinicalSummaryRecord(patient_id=p.id, summary_text="Odbijeni sazetak", status="rejected", generated_by="physician")
    db.add(rejected)
    db.commit()

    summary = client.get(f"/api/patients/{p.id}/clinical-summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["reviewed_summary"] is None
    assert summary.json()["draft_summary"] is None


def test_summary_status_validation_rejects_unknown_status(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    response = client.patch(f"/api/patients/{p.id}/clinical-summary", headers=headers, json={"status": "official_truth"})
    assert response.status_code == 422


def test_readiness_detects_stale_patient_summary(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    clinical_document(db, p, physician_reviewed=True)

    response = client.get("/api/readiness", headers=headers)
    assert response.status_code == 200
    check = next(item for item in response.json()["checks"] if item["key"] == "patient_summary_stale")
    assert check["status"] == "warning"
    assert check["target_path"] == "/patients"


def test_stale_summary_detects_new_reviewed_document(client, db, auth_setup):
    headers = auth_headers(client)
    p = patient(db)
    old_doc = clinical_document(db, p, physician_reviewed=True)
    old_doc.updated_at = datetime(2026, 7, 1, 9, 0)
    db.commit()

    draft = client.post(f"/api/patients/{p.id}/clinical-summary/generate-draft", headers=headers)
    assert draft.status_code == 200
    reviewed = client.post(f"/api/patients/{p.id}/clinical-summary/review", headers=headers)
    assert reviewed.status_code == 200
    record = db.get(PatientClinicalSummaryRecord, reviewed.json()["id"])
    record.updated_at = datetime(2026, 7, 2, 9, 0)

    new_doc = clinical_document(db, p, physician_reviewed=True)
    new_doc.updated_at = datetime(2026, 7, 3, 9, 0)
    db.commit()

    response = client.get("/api/readiness", headers=headers)
    assert response.status_code == 200
    check = next(item for item in response.json()["checks"] if item["key"] == "patient_summary_stale")
    assert check["status"] == "warning"
    assert check["count"] == 1
