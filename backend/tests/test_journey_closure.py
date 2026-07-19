from tests.conftest import login_token
from tests.factories import appointment
from datetime import datetime, timedelta
from app.models.domain import JourneyActivity, PatientJourney

def headers(client): return {"Authorization": f"Bearer {login_token(client, 'admin@test.local')}"}

def completed_encounter(client, db):
    h=headers(client); appt=appointment(db)
    journey=client.post("/api/patient-journeys",headers=h,json={"appointment_id":appt.id,"intake_channel":"manual","initial_stage":"booked"}).json()
    for stage in ("ready_for_arrival","arrived","check_in_review"):
        assert client.post(f"/api/patient-journeys/{journey['id']}/transition",headers=h,json={"target_stage":stage}).status_code==200
    client.patch(f"/api/patient-journeys/{journey['id']}/statuses",headers=h,json={"check_in_status":"ready"})
    client.post(f"/api/patient-journeys/{journey['id']}/transition",headers=h,json={"target_stage":"ready_for_clinician"})
    client.post(f"/api/patient-journeys/{journey['id']}/encounter",headers=h)
    client.patch(f"/api/patient-journeys/{journey['id']}/encounter",headers=h,json={"procedure_findings":"Sintetički nalaz"})
    assert client.post(f"/api/patient-journeys/{journey['id']}/encounter/complete",headers=h).status_code==200
    activity=journey["activities"][0]
    for target in ("ready","in_progress","completed"):
        assert client.post(f"/api/patient-journeys/{journey['id']}/activities/{activity['id']}/transition",headers=h,json={"target_status":target}).status_code==200
    return journey,h

def test_legacy_consumables_endpoint_never_completes_activity(client,db,auth_setup):
    h=headers(client);appt=appointment(db)
    journey=client.post("/api/patient-journeys",headers=h,json={"appointment_id":appt.id,"intake_channel":"manual","initial_stage":"booked"}).json()
    visit=db.get(PatientJourney,journey["id"])
    visit.current_stage="procedure_completed";visit.encounter_status="completed"
    db.commit()
    response=client.post(f"/api/patient-journeys/{visit.id}/consumables/confirm",headers=h,json={"not_applicable":True})
    assert response.status_code==409
    db.refresh(visit.activities[0])
    assert visit.activities[0].status=="planned"

def test_explicit_no_consumables_invoice_payment_and_closure(client,db,auth_setup):
    journey,h=completed_encounter(client,db);url=f"/api/patient-journeys/{journey['id']}"
    response=client.post(f"{url}/consumables/confirm",headers=h,json={"not_applicable":True});assert response.status_code==200 and response.json()["stage"]=="awaiting_billing"
    response=client.post(f"{url}/billing/prepare",headers=h);assert response.status_code==200 and response.json()["invoice"]["status"]=="issued"
    total=response.json()["invoice"]["total"]
    response=client.post(f"{url}/payments",headers=h,json={"amount":total,"method":"card","reference":"SYNTHETIC"});assert response.status_code==200 and response.json()["payment_status"]=="paid", (total,response.json()["invoice"]["total"],response.json()["invoice"]["paid"])
    assert response.json()["stage"]=="completed"

def test_cannot_close_with_unresolved_payment(client,db,auth_setup):
    journey,h=completed_encounter(client,db);url=f"/api/patient-journeys/{journey['id']}"
    client.post(f"{url}/consumables/confirm",headers=h,json={"not_applicable":True});client.post(f"{url}/billing/prepare",headers=h)
    assert client.post(f"{url}/close",headers=h).status_code==409

def test_unsigned_required_activity_report_blocks_billing(client,db,auth_setup):
    journey,h=completed_encounter(client,db);url=f"/api/patient-journeys/{journey['id']}"
    visit=db.get(PatientJourney,journey["id"])
    visit.activities[0].form_resolution_status="resolved"
    db.commit()
    assert client.post(f"{url}/consumables/confirm",headers=h,json={"not_applicable":True}).status_code==200
    blocked=client.post(f"{url}/billing/prepare",headers=h)
    assert blocked.status_code==409
    assert "potpisani" in blocked.json()["detail"]

def test_payment_may_be_explicitly_deferred_with_reason(client,db,auth_setup):
    journey,h=completed_encounter(client,db);url=f"/api/patient-journeys/{journey['id']}"
    client.post(f"{url}/consumables/confirm",headers=h,json={"not_applicable":True});client.post(f"{url}/billing/prepare",headers=h)
    response=client.post(f"{url}/payments/defer",headers=h,json={"reason":"Sintetički ugovorni platitelj"})
    assert response.status_code==200 and response.json()["stage"]=="completed"

def test_multi_activity_consumables_and_invoice_are_activity_linked_and_idempotent(client,db,auth_setup):
    journey,h=completed_encounter(client,db);url=f"/api/patient-journeys/{journey['id']}"
    visit=db.get(PatientJourney,journey["id"])
    primary=visit.activities[0]
    primary.status="completed"
    second=JourneyActivity(journey_id=visit.id,service_id=primary.service_id,activity_key="second",activity_kind=primary.activity_kind,specialty_key=primary.specialty_key,clinic_id=primary.clinic_id,primary_provider_id=primary.primary_provider_id,room_id=primary.room_id,sequence=2,required=True,planned_start=primary.planned_end,planned_end=primary.planned_end+timedelta(minutes=30),status="completed",form_resolution_status="not_required")
    db.add(second);db.commit();db.refresh(second)
    first=client.post(f"{url}/activities/{primary.id}/consumables/confirm",headers=h,json={"not_applicable":True})
    assert first.status_code==200 and first.json()["stage"]=="procedure_completed"
    second_response=client.post(f"{url}/activities/{second.id}/consumables/confirm",headers=h,json={"not_applicable":True})
    assert second_response.status_code==200 and second_response.json()["stage"]=="awaiting_billing"
    invoice=client.post(f"{url}/billing/prepare",headers=h)
    assert invoice.status_code==200
    lines=invoice.json()["invoice"]["lines"]
    assert {line["activity_id"] for line in lines}=={primary.id,second.id}
    retry=client.post(f"{url}/billing/prepare",headers=h)
    assert retry.status_code==200 and len(retry.json()["invoice"]["lines"])==2
