from tests.conftest import login_token
from tests.factories import appointment, patient, provider, room, service


def headers(client):
    return {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}


def create_journey(client, appt):
    response = client.post(
        "/api/patient-journeys",
        headers=headers(client),
        json={"appointment_id": appt.id, "intake_channel": "manual", "initial_stage": "booked"},
    )
    assert response.status_code == 200
    return response.json()


def test_daily_dashboard_returns_one_aggregated_row_per_journey(client, db, auth_setup):
    appt = appointment(db)
    journey = create_journey(client, appt)
    response = client.get("/api/dashboard/day?selected_date=2026-07-06", headers=headers(client))
    assert response.status_code == 200
    body = response.json()
    assert body["date"] == "2026-07-06"
    assert body["rows"][0]["journey_id"] == journey["id"]
    assert body["rows"][0]["service_name"] == appt.service.name
    assert set(("document_status", "preparation_status", "check_in_status", "billing_status", "payment_status", "blocker_status")).issubset(body["rows"][0])


def test_daily_dashboard_filters_server_side_and_exposes_blockers(client, db, auth_setup):
    first = appointment(db, patient_obj=patient(db, "SyntheticAlpha"), provider_obj=provider(db, "dr. Alpha"), room_obj=room(db, "Room Alpha"), service_obj=service(db, "Service Alpha"))
    second = appointment(db, patient_obj=patient(db, "SyntheticBeta"), provider_obj=provider(db, "dr. Beta"), room_obj=room(db, "Room Beta"), service_obj=service(db, "Service Beta"))
    first_journey = create_journey(client, first)
    create_journey(client, second)
    client.post(
        f"/api/patient-journeys/{first_journey['id']}/blockers",
        headers=headers(client),
        json={"blocker_key": "missing_source", "category": "documents", "title": "Nedostaje sintetički dokument", "is_clinical": False},
    )
    response = client.get("/api/dashboard/day?selected_date=2026-07-06&blocker=true&q=Alpha", headers=headers(client))
    assert response.status_code == 200
    assert len(response.json()["rows"]) == 1
    assert response.json()["rows"][0]["blocker_labels"] == ["Nedostaje sintetički dokument"]


def test_daily_dashboard_requires_journey_read_permission(client, db, auth_setup):
    response = client.get(
        "/api/dashboard/day?selected_date=2026-07-06",
        headers={"Authorization": f"Bearer {login_token(client, 'limited@test.local')}"},
    )
    assert response.status_code == 403
