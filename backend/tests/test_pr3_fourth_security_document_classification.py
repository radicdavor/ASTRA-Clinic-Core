from app.models.domain import ClinicalDocument
from tests.conftest import login_token
from tests.factories import patient


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def test_manual_clinical_document_starts_unclassified(client, db, auth_setup):
    p = patient(db)
    response = client.post(
        "/api/clinical-documents",
        headers=auth_headers(client),
        json={
            "patient_id": p.id,
            "source_type": "external",
            "document_type": "other",
            "title": "Sintetički ručni dokument",
        },
    )

    assert response.status_code == 200
    assert response.json()["record_classification"] == "unclassified"
    assert db.get(ClinicalDocument, response.json()["id"]).record_classification == (
        "unclassified"
    )
    assert (
        client.get(
            f"/api/clinical-documents/{response.json()['id']}",
            headers=auth_headers(client),
        ).status_code
        == 403
    )

    classified = client.post(
        f"/api/clinical-documents/{response.json()['id']}/classification/review",
        headers=auth_headers(client),
        json={
            "record_classification": "clinical",
            "note": "Ljudski potvrđena klasifikacija sintetičkog izvora.",
        },
    )
    assert classified.status_code == 200
    assert classified.json()["record_classification"] == "clinical"


def test_clinical_document_orm_default_is_fail_closed(db):
    p = patient(db)
    document = ClinicalDocument(
        patient_id=p.id,
        source_type="external",
        document_type="other",
        title="Sintetički dokument bez eksplicitne klasifikacije",
    )
    db.add(document)
    db.flush()

    assert document.record_classification == "unclassified"
