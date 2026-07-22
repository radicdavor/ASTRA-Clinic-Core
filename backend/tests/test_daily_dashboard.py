from tests.conftest import login_token
from app.core.security import hash_password
from app.models.domain import ClinicMembership, PatientClinicAssociation, Role, User
from tests.factories import appointment, clinic, patient, provider, room, service


def headers(client):
    return {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}


def create_journey(client, appt):
    response = client.post(
        "/api/patient-journeys",
        headers={**headers(client), "X-Clinic-Id": str(appt.clinic_id)},
        json={"appointment_id": appt.id, "intake_channel": "manual", "initial_stage": "booked"},
    )
    assert response.status_code == 200
    return response.json()


def scope_appointment(db, auth_setup, appt, clinic_obj=None):
    clinic_obj = clinic_obj or auth_setup["clinic"]
    appt.clinic_id = clinic_obj.id
    appt.room.clinic_id = clinic_obj.id
    if not db.query(ClinicMembership).filter_by(user_id=auth_setup["admin"].id, clinic_id=clinic_obj.id).first():
        db.add(ClinicMembership(user_id=auth_setup["admin"].id, clinic_id=clinic_obj.id, created_by_user_id=auth_setup["admin"].id))
    if not db.query(PatientClinicAssociation).filter_by(patient_id=appt.patient_id, clinic_id=clinic_obj.id).first():
        db.add(PatientClinicAssociation(patient_id=appt.patient_id, clinic_id=clinic_obj.id, created_by_user_id=auth_setup["admin"].id))
    db.commit()
    return appt


def test_daily_dashboard_returns_one_aggregated_row_per_journey(client, db, auth_setup, sql_query_counter):
    appt = appointment(db)
    scope_appointment(db, auth_setup, appt)
    journey = create_journey(client, appt)
    request_headers = headers(client)
    with sql_query_counter.track() as query_count:
        response = client.get("/api/dashboard/day?selected_date=2026-07-06", headers=request_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["date"] == "2026-07-06"
    assert body["rows"][0]["journey_id"] == journey["id"]
    assert body["rows"][0]["service_name"] == appt.service.name
    assert body["scope"] == "all"
    assert body["can_filter_clinician"] is True
    assert set(("document_status", "preparation_status", "check_in_status", "billing_status", "payment_status", "blocker_status")).issubset(body["rows"][0])
    assert body["rows"][0]["operational_status"] == "waiting_arrival"
    assert body["rows"][0]["operational_status_label"] == "Čeka dolazak"
    assert body["rows"][0]["operational_status_severity"] == "neutral"
    assert body["rows"][0]["operational_status_reasons"][0]["code"] == "patient_not_arrived"
    assert isinstance(body["rows"][0]["allowed_actions"], list)
    assert body["rows"][0]["activity_count"] == 1
    assert body["rows"][0]["activities"][0]["service_name"] == appt.service.name
    assert query_count.count <= 12


def test_daily_dashboard_shows_consultation_and_gastroscopy_as_one_arrival(client, db, auth_setup):
    consultation = appointment(
        db,
        patient_obj=patient(db, "Sintetički Višestruki"),
        provider_obj=provider(db, "dr. Demo Gastro"),
        room_obj=room(db, "Demo ordinacija"),
        service_obj=service(db, "Prvi gastroenterološki pregled"),
    )
    scope_appointment(db, auth_setup, consultation)
    journey = create_journey(client, consultation)
    gastroscopy = service(db, "Gastroskopija")
    endoscopy_room = room(db, "Demo endoskopija")
    endoscopy_room.clinic_id = auth_setup["clinic"].id
    db.commit()
    second = client.post(
        f"/api/patient-journeys/{journey['id']}/activities",
        headers=headers(client),
        json={
            "service_id": gastroscopy.id,
            "provider_id": consultation.provider_id,
            "room_id": endoscopy_room.id,
            "date": "2026-07-06",
            "start_time": "09:30:00",
            "end_time": "10:00:00",
            "activity_key": "gastroscopy",
            "activity_kind": "gastroscopy",
            "specialty_key": "gastroenterology",
            "required": True,
        },
    )
    assert second.status_code == 201

    response = client.get("/api/dashboard/day?selected_date=2026-07-06&q=Višestruki", headers=headers(client))
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert len(rows) == 1
    assert rows[0]["activity_count"] == 2
    assert [item["service_name"] for item in rows[0]["activities"]] == [
        "Prvi gastroenterološki pregled",
        "Gastroskopija",
    ]
    assert [item["room_name"] for item in rows[0]["activities"]] == [
        "Demo ordinacija",
        "Demo endoskopija",
    ]


def test_daily_dashboard_filters_server_side_and_exposes_blockers(client, db, auth_setup):
    first = appointment(db, patient_obj=patient(db, "SyntheticAlpha"), provider_obj=provider(db, "dr. Alpha"), room_obj=room(db, "Room Alpha"), service_obj=service(db, "Service Alpha"))
    second = appointment(db, patient_obj=patient(db, "SyntheticBeta"), provider_obj=provider(db, "dr. Beta"), room_obj=room(db, "Room Beta"), service_obj=service(db, "Service Beta"))
    scope_appointment(db, auth_setup, first)
    scope_appointment(db, auth_setup, second)
    first_journey = create_journey(client, first)
    create_journey(client, second)
    client.post(
        f"/api/patient-journeys/{first_journey['id']}/blockers",
        headers=headers(client),
        json={"blocker_key": "missing_source", "category": "documents", "title": "Nedostaje sintetički dokument", "details": "Nalaz nije priložen uz termin.", "is_clinical": False},
    )
    response = client.get("/api/dashboard/day?selected_date=2026-07-06&blocker=true&q=Alpha", headers=headers(client))
    assert response.status_code == 200
    assert len(response.json()["rows"]) == 1
    assert response.json()["rows"][0]["blocker_labels"] == ["Nedostaje sintetički dokument"]
    assert response.json()["rows"][0]["operational_status_severity"] == "critical"
    assert response.json()["rows"][0]["operational_status_reasons"][0]["code"] == "open_blocker"
    assert response.json()["rows"][0]["blockers"] == [{"id": response.json()["rows"][0]["blockers"][0]["id"], "title": "Nedostaje sintetički dokument", "details": "Nalaz nije priložen uz termin.", "is_clinical": False}]


def test_daily_dashboard_requires_journey_read_permission(client, db, auth_setup):
    response = client.get(
        "/api/dashboard/day?selected_date=2026-07-06",
        headers={"Authorization": f"Bearer {login_token(client, 'limited@test.local')}"},
    )
    assert response.status_code == 403


def test_physician_sees_only_own_daily_schedule_and_can_filter_working_clinics(client, db, auth_setup):
    first_clinic = clinic(db, "Klinika Sjever")
    second_clinic = clinic(db, "Klinika Jug")
    first_room = room(db, "Ordinacija Sjever")
    first_room.clinic_id = first_clinic.id
    second_room = room(db, "Ordinacija Jug")
    second_room.clinic_id = second_clinic.id
    doctor = provider(db, "dr. Vlastiti Raspored")
    doctor.email = "doctor@test.local"
    other_doctor = provider(db, "dr. Drugi Raspored")
    own_first = appointment(db, patient_obj=patient(db, "Prvi"), provider_obj=doctor, room_obj=first_room, service_obj=service(db, "Prva usluga"))
    own_second = appointment(db, patient_obj=patient(db, "Drugi"), provider_obj=doctor, room_obj=second_room, service_obj=service(db, "Druga usluga"))
    other = appointment(db, patient_obj=patient(db, "Tuđi"), provider_obj=other_doctor, room_obj=first_room, service_obj=service(db, "Tuđa usluga"))
    scope_appointment(db, auth_setup, own_first, first_clinic)
    scope_appointment(db, auth_setup, own_second, second_clinic)
    scope_appointment(db, auth_setup, other, first_clinic)
    for appt in (own_first, own_second, other):
        create_journey(client, appt)

    journey_read = next(permission for permission in auth_setup["admin"].role.permissions if permission.name == "journey.read")
    physician_role = Role(name="physician", description="Physician", permissions=[journey_read])
    physician_user = User(email=doctor.email, full_name=doctor.full_name, password_hash=hash_password("secret"), role=physician_role)
    db.add_all([physician_role, physician_user])
    db.flush()
    db.add_all(
        [
            ClinicMembership(user_id=physician_user.id, clinic_id=first_clinic.id, created_by_user_id=auth_setup["admin"].id),
            ClinicMembership(user_id=physician_user.id, clinic_id=second_clinic.id, created_by_user_id=auth_setup["admin"].id),
        ]
    )
    db.commit()
    physician_headers = {"Authorization": f"Bearer {login_token(client, doctor.email)}"}

    response = client.get("/api/dashboard/day?selected_date=2026-07-06", headers=physician_headers)
    assert response.status_code == 409

    response = client.get("/api/dashboard/day?selected_date=2026-07-06", headers={**physician_headers, "X-Clinic-Id": str(first_clinic.id)})
    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "own_clinician"
    assert body["scope_label"] == doctor.full_name
    assert body["scoped_clinician_id"] == doctor.id
    assert body["can_filter_clinician"] is False
    assert {row["patient_name"] for row in body["rows"]} == {"Prvi Patient"}
    assert {item["name"] for item in body["available_clinics"]} == {"Klinika Sjever"}

    filtered = client.get(f"/api/dashboard/day?selected_date=2026-07-06&clinic_id={second_clinic.id}", headers={**physician_headers, "X-Clinic-Id": str(second_clinic.id)})
    assert [row["patient_name"] for row in filtered.json()["rows"]] == ["Drugi Patient"]
    forbidden = client.get(f"/api/dashboard/day?selected_date=2026-07-06&clinician_id={other_doctor.id}", headers={**physician_headers, "X-Clinic-Id": str(first_clinic.id)})
    assert forbidden.status_code == 403


def test_physician_without_provider_link_never_falls_back_to_all_patients(client, db, auth_setup):
    journey_read = next(permission for permission in auth_setup["admin"].role.permissions if permission.name == "journey.read")
    physician_role = Role(name="demo_physician", description="Demo physician", permissions=[journey_read])
    unlinked = User(email="unlinked@test.local", full_name="Unlinked", password_hash=hash_password("secret"), role=physician_role)
    db.add_all([physician_role, unlinked])
    db.flush()
    db.add(ClinicMembership(user_id=unlinked.id, clinic_id=auth_setup["clinic"].id, created_by_user_id=auth_setup["admin"].id))
    db.commit()
    response = client.get(
        "/api/dashboard/day?selected_date=2026-07-06",
        headers={"Authorization": f"Bearer {login_token(client, unlinked.email)}"},
    )
    assert response.status_code == 403
    assert "nije povezan" in response.json()["detail"]
