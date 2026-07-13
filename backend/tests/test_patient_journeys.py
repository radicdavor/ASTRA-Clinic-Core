from app.models.domain import AuditLog,JourneyEvent
from tests.conftest import login_token
from tests.factories import appointment,patient,provider,room,service

def headers(client,email="admin@test.local"): return {"Authorization":f"Bearer {login_token(client,email)}"}

def test_all_intake_channels_create_same_canonical_contract(client,db,auth_setup):
    for index,channel in enumerate(("web","ai_secretary","manual")):
        appt=appointment(db,patient_obj=patient(db,f"Synthetic{index}"),provider_obj=provider(db,f"dr. Synthetic {index}"),room_obj=room(db,f"Synthetic room {index}"),service_obj=service(db,f"Synthetic service {index}"))
        response=client.post("/api/patient-journeys",headers=headers(client),json={"appointment_id":appt.id,"intake_channel":channel,"initial_stage":"requested" if channel!="manual" else "booked"})
        assert response.status_code==200
        body=response.json();assert body["appointment_id"]==appt.id and body["patient_id"]==appt.patient_id and body["intake_channel"]==channel
        assert set(("document_status","preparation_status","check_in_status","encounter_status","billing_status","payment_status")).issubset(body)
    assert db.query(JourneyEvent).filter(JourneyEvent.event_type=="journey_created").count()==3

def test_state_machine_rejects_impossible_transition_and_audits_valid_one(client,db,auth_setup):
    appt=appointment(db);created=client.post("/api/patient-journeys",headers=headers(client),json={"appointment_id":appt.id,"intake_channel":"manual","initial_stage":"booked"}).json();journey_id=created["id"]
    invalid=client.post(f"/api/patient-journeys/{journey_id}/transition",headers=headers(client),json={"target_stage":"in_encounter"})
    assert invalid.status_code==409
    valid=client.post(f"/api/patient-journeys/{journey_id}/transition",headers=headers(client),json={"target_stage":"ready_for_arrival","reason":"Administrativna priprema završena"})
    assert valid.status_code==200 and valid.json()["current_stage"]=="ready_for_arrival"
    assert db.query(AuditLog).filter(AuditLog.entity_type=="PatientJourney",AuditLog.action=="transition").count()==1

def test_open_blocker_prevents_clinical_progress_until_human_resolution(client,db,auth_setup):
    appt=appointment(db);journey=client.post("/api/patient-journeys",headers=headers(client),json={"appointment_id":appt.id,"intake_channel":"manual"}).json();jid=journey["id"]
    blocker=client.post(f"/api/patient-journeys/{jid}/blockers",headers=headers(client),json={"blocker_key":"anticoagulant_review","category":"precondition","title":"Potrebna liječnička provjera","is_clinical":True}).json()
    client.post(f"/api/patient-journeys/{jid}/transition",headers=headers(client),json={"target_stage":"ready_for_arrival"})
    client.post(f"/api/patient-journeys/{jid}/transition",headers=headers(client),json={"target_stage":"arrived"})
    client.post(f"/api/patient-journeys/{jid}/transition",headers=headers(client),json={"target_stage":"check_in_review"})
    client.patch(f"/api/patient-journeys/{jid}/statuses",headers=headers(client),json={"check_in_status":"ready"})
    assert client.post(f"/api/patient-journeys/{jid}/transition",headers=headers(client),json={"target_stage":"ready_for_clinician"}).status_code==409
    assert client.post(f"/api/patient-journeys/{jid}/blockers/{blocker['id']}/resolve",headers=headers(client),json={"resolution_note":"Liječnik pregledao; odluka dokumentirana"}).status_code==200
    assert client.post(f"/api/patient-journeys/{jid}/transition",headers=headers(client),json={"target_stage":"ready_for_clinician"}).status_code==200

def test_journey_endpoints_require_dedicated_permission(client,db,auth_setup):
    appt=appointment(db)
    response=client.post("/api/patient-journeys",headers=headers(client,"limited@test.local"),json={"appointment_id":appt.id,"intake_channel":"manual"})
    assert response.status_code==403
