from tests.conftest import login_token
from tests.factories import appointment

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
    return journey,h

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

def test_payment_may_be_explicitly_deferred_with_reason(client,db,auth_setup):
    journey,h=completed_encounter(client,db);url=f"/api/patient-journeys/{journey['id']}"
    client.post(f"{url}/consumables/confirm",headers=h,json={"not_applicable":True});client.post(f"{url}/billing/prepare",headers=h)
    response=client.post(f"{url}/payments/defer",headers=h,json={"reason":"Sintetički ugovorni platitelj"})
    assert response.status_code==200 and response.json()["stage"]=="completed"
