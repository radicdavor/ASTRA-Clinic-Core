from datetime import date, datetime, time

from app.models.domain import Appointment, ClinicalEpisode, Clinic, Institution, JourneyActivity, LabOrder, Patient, PatientClinicAssociation, PatientJourney, Provider, Room, Service, Therapy, WorkflowTask
from tests.conftest import login_token


def headers(client, auth_setup):
    return {
        "Authorization": f"Bearer {login_token(client, 'admin@test.local')}",
        "X-Clinic-Id": str(auth_setup["clinic"].id),
    }


def foreign_clinical_records(db, auth_setup):
    institution = Institution(name="Foreign clinical institution")
    clinic = Clinic(name="Foreign clinical clinic", institution=institution)
    patient = Patient(first_name="Global", last_name="Identity")
    db.add_all([institution, clinic, patient])
    db.flush()
    db.add_all(
        [
            PatientClinicAssociation(patient_id=patient.id, clinic_id=auth_setup["clinic"].id),
            PatientClinicAssociation(patient_id=patient.id, clinic_id=clinic.id),
        ]
    )
    episode = ClinicalEpisode(
        patient_id=patient.id,
        institution_id=institution.id,
        title="FOREIGN_EPISODE_SENTINEL",
        episode_type="general",
        status="active",
        priority="routine",
        start_date=date(2026, 7, 1),
    )
    db.add(episode)
    db.flush()
    lab = LabOrder(patient_id=patient.id, institution_id=institution.id, episode_id=episode.id, ordered_at=date(2026, 7, 22), status="ordered")
    therapy = Therapy(
        patient_id=patient.id,
        institution_id=institution.id,
        episode_id=episode.id,
        name="FOREIGN_THERAPY_SENTINEL",
        instructions="FOREIGN_INSTRUCTIONS_SENTINEL",
        start_date=date(2026, 7, 22),
        status="active",
    )
    task = WorkflowTask(
        patient_id=patient.id,
        institution_id=institution.id,
        episode_id=episode.id,
        title="FOREIGN_TASK_SENTINEL",
        status="open",
        priority="routine",
    )
    db.add_all([lab, therapy, task])
    db.flush()
    return patient, lab, therapy, task


def test_laboratory_is_not_global_patient_scoped(client, db, auth_setup):
    patient, lab, _, _ = foreign_clinical_records(db, auth_setup)
    auth = headers(client, auth_setup)

    listed = client.get(f"/api/laboratory/orders?patient_id={patient.id}", headers=auth)
    detail = client.get(f"/api/laboratory/orders/{lab.id}", headers=auth)
    mutated = client.post(f"/api/laboratory/orders/{lab.id}/collect", headers=auth, json={"specimen_type": "blood"})

    assert listed.status_code == 200
    assert listed.json() == []
    assert detail.status_code == 404
    assert mutated.status_code == 404


def test_therapy_is_not_global_patient_scoped(client, db, auth_setup):
    patient, _, therapy, _ = foreign_clinical_records(db, auth_setup)
    auth = headers(client, auth_setup)

    listed = client.get(f"/api/therapies?patient_id={patient.id}", headers=auth)
    mutated = client.post(f"/api/therapies/{therapy.id}/stop", headers=auth, json={"reason": "test"})

    assert listed.status_code == 200
    assert listed.json() == []
    assert mutated.status_code == 404


def test_workflow_tasks_are_not_global_patient_scoped(client, db, auth_setup):
    patient, _, _, task = foreign_clinical_records(db, auth_setup)
    auth = headers(client, auth_setup)

    listed = client.get(f"/api/workflow-tasks?patient_id={patient.id}", headers=auth)
    detail = client.get(f"/api/workflow-tasks/{task.id}", headers=auth)
    mutated = client.patch(f"/api/workflow-tasks/{task.id}", headers=auth, json={"status": "in_progress"})

    assert listed.status_code == 200
    assert listed.json() == []
    assert detail.status_code == 404
    assert mutated.status_code == 404


def test_journey_child_surfaces_require_active_clinic_scope(client, db, auth_setup):
    institution = Institution(name="Foreign journey institution")
    clinic = Clinic(name="Foreign journey clinic", institution=institution)
    patient = Patient(first_name="Foreign", last_name="Journey")
    provider = Provider(full_name="Foreign Provider", specialty="Test", clinic=clinic)
    room = Room(name="Foreign Room", type="test", clinic=clinic)
    service = Service(name="Foreign Service", duration_minutes=30, price=100)
    db.add_all([institution, clinic, patient, provider, room, service])
    db.flush()
    appointment = Appointment(
        patient_id=patient.id,
        clinic_id=clinic.id,
        provider_id=provider.id,
        room_id=room.id,
        service_id=service.id,
        date=date(2026, 7, 22),
        start_time=time(9, 0),
        end_time=time(9, 30),
        duration_minutes=30,
        status="scheduled",
    )
    db.add(appointment)
    db.flush()
    journey = PatientJourney(
        patient_id=patient.id,
        appointment_id=appointment.id,
        clinic_id=clinic.id,
        current_stage="booked",
        intake_channel="manual",
    )
    db.add(journey)
    db.flush()
    activity = JourneyActivity(
        journey_id=journey.id,
        appointment_id=appointment.id,
        service_id=service.id,
        activity_key="primary",
        activity_kind="procedure",
        specialty_key="test",
        clinic_id=clinic.id,
        primary_provider_id=provider.id,
        room_id=room.id,
        sequence=1,
        required=True,
        planned_start=datetime(2026, 7, 22, 9, 0),
        planned_end=datetime(2026, 7, 22, 9, 30),
        status="planned",
    )
    db.add(activity)
    db.flush()
    auth = headers(client, auth_setup)

    urls = [
        f"/api/patient-journeys/{journey.id}/activities",
        f"/api/patient-journeys/{journey.id}/check-in",
        f"/api/patient-journeys/{journey.id}/preparation",
        f"/api/patient-journeys/{journey.id}/encounter",
        f"/api/patient-journeys/{journey.id}/pathology-cases",
        f"/api/patient-journeys/{journey.id}/activities/{activity.id}/form",
        f"/api/appointments/{appointment.id}/clinical-readiness-preview",
    ]
    for url in urls:
        assert client.get(url, headers=auth).status_code == 404
