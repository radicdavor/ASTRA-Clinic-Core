from app.models.domain import CommunicationEvent, DocumentRequest, JourneyEvent, JourneyReminder
from tests.conftest import login_token
from tests.factories import appointment


def headers(client, email="admin@test.local"):
    return {"Authorization": f"Bearer {login_token(client, email)}"}


def create_journey(client, db):
    appt = appointment(db)
    response = client.post(
        "/api/patient-journeys",
        headers=headers(client),
        json={"appointment_id": appt.id, "intake_channel": "manual", "initial_stage": "booked"},
    )
    assert response.status_code == 200
    return response.json()


def create_preparation_template(client, approved=True):
    response = client.post(
        "/api/preparation-templates",
        headers=headers(client),
        json={
            "template_key": "gastroscopy-standard",
            "name": "Sintetička priprema za gastroskopiju",
            "procedure_type": "gastroscopy",
            "version": "1.0",
            "patient_instructions": "Sintetičke upute za testiranje; liječnik odlučuje.",
            "requirements_json": [
                {"key": "fasting", "label": "Post potvrđen"},
                {"key": "medication_review", "label": "Pregled terapije"},
            ],
            "approved": approved,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_approved_preparation_assignment_schedules_default_reminders(client, db, auth_setup):
    journey = create_journey(client, db)
    template = create_preparation_template(client)
    response = client.post(
        f"/api/patient-journeys/{journey['id']}/preparation",
        headers=headers(client),
        json={"template_id": template["id"], "channel": "email"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "assigned"
    assert response.json()["requirement_states_json"] == {
        "fasting": "not_confirmed",
        "medication_review": "not_confirmed",
    }
    reminders = db.query(JourneyReminder).filter_by(journey_id=journey["id"]).all()
    assert [item.reminder_type for item in reminders] == [
        "appointment_reminder",
        "preparation_reminder",
    ]


def test_unapproved_preparation_template_cannot_be_assigned(client, db, auth_setup):
    journey = create_journey(client, db)
    template = create_preparation_template(client, approved=False)
    response = client.post(
        f"/api/patient-journeys/{journey['id']}/preparation",
        headers=headers(client),
        json={"template_id": template["id"], "channel": "manual"},
    )
    assert response.status_code == 422
    assert "odobren" in response.json()["detail"]


def test_clinician_review_requirement_is_not_automatically_cleared(client, db, auth_setup):
    journey = create_journey(client, db)
    template = create_preparation_template(client)
    client.post(
        f"/api/patient-journeys/{journey['id']}/preparation",
        headers=headers(client),
        json={"template_id": template["id"], "channel": "manual"},
    )
    response = client.patch(
        f"/api/patient-journeys/{journey['id']}/preparation/requirements",
        headers=headers(client),
        json={"requirement_key": "medication_review", "state": "requires_clinician_review"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "review_required"
    assert response.json()["requirement_states_json"]["medication_review"] == "requires_clinician_review"


def test_demo_dispatch_records_sent_but_never_claims_delivery(client, db, auth_setup):
    journey = create_journey(client, db)
    template = create_preparation_template(client)
    client.post(
        f"/api/patient-journeys/{journey['id']}/preparation",
        headers=headers(client),
        json={"template_id": template["id"], "channel": "sms"},
    )
    reminder = db.query(JourneyReminder).filter_by(journey_id=journey["id"]).first()
    response = client.post(
        f"/api/patient-journeys/{journey['id']}/reminders/{reminder.id}/dispatch",
        headers=headers(client),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    assert response.json()["delivered_at"] is None
    assert db.query(CommunicationEvent).filter_by(journey_id=journey["id"], status="sent").count() == 1
    assert db.query(JourneyEvent).filter_by(journey_id=journey["id"], event_type="reminder_dispatched").count() == 1


def test_forms_require_approved_version_and_document_request_updates_status(client, db, auth_setup):
    journey = create_journey(client, db)
    form = client.post(
        "/api/form-templates",
        headers=headers(client),
        json={
            "template_key": "health-questionnaire",
            "name": "Sintetički zdravstveni upitnik",
            "version": "1.0",
            "fields_json": [{"key": "allergies", "type": "text"}],
            "approved": True,
        },
    )
    assert form.status_code == 200
    requested_form = client.post(
        f"/api/patient-journeys/{journey['id']}/forms",
        headers=headers(client),
        json={"template_id": form.json()["id"]},
    )
    assert requested_form.status_code == 200
    answer = client.put(
        f"/api/patient-journeys/{journey['id']}/forms/{requested_form.json()['id']}",
        headers=headers(client),
        json={"answers_json": {"allergies": "Nije navedeno u sintetičkom testu"}},
    )
    assert answer.status_code == 200
    assert answer.json()["status"] == "completed"
    document = client.post(
        f"/api/patient-journeys/{journey['id']}/document-requests",
        headers=headers(client),
        json={"document_type": "laboratory", "title": "Laboratorijski nalaz", "mandatory": True},
    )
    assert document.status_code == 200
    assert db.query(DocumentRequest).filter_by(journey_id=journey["id"], status="requested").count() == 1
    detail = client.get(f"/api/patient-journeys/{journey['id']}", headers=headers(client))
    assert detail.json()["document_status"] == "requested"


def test_preparation_routes_require_dedicated_permissions(client, db, auth_setup):
    response = client.post(
        "/api/preparation-templates",
        headers=headers(client, "limited@test.local"),
        json={
            "template_key": "denied",
            "name": "Zabranjeno",
            "procedure_type": "test",
            "version": "1",
            "patient_instructions": "Nije dopušteno.",
        },
    )
    assert response.status_code == 403
