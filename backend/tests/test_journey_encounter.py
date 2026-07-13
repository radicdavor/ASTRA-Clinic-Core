from tests.conftest import login_token
from tests.factories import appointment
def headers(client): return {"Authorization":f"Bearer {login_token(client,'admin@test.local')}"}
def journey(client,db,ready=True):
 h=headers(client);appt=appointment(db);body=client.post("/api/patient-journeys",headers=h,json={"appointment_id":appt.id,"intake_channel":"manual","initial_stage":"booked"}).json()
 if ready:
  for stage in ("ready_for_arrival","arrived","check_in_review"): assert client.post(f"/api/patient-journeys/{body['id']}/transition",headers=h,json={"target_stage":stage}).status_code==200
  client.patch(f"/api/patient-journeys/{body['id']}/statuses",headers=h,json={"check_in_status":"ready"})
  assert client.post(f"/api/patient-journeys/{body['id']}/transition",headers=h,json={"target_stage":"ready_for_clinician"}).status_code==200
 return body,h
def test_encounter_requires_completed_check_in(client,db,auth_setup):
 item,h=journey(client,db,False);response=client.post(f"/api/patient-journeys/{item['id']}/encounter",headers=h);assert response.status_code==409
def test_encounter_note_is_human_written_and_completed_explicitly(client,db,auth_setup):
 item,h=journey(client,db);opened=client.post(f"/api/patient-journeys/{item['id']}/encounter",headers=h);assert opened.status_code==200 and opened.json()["status"]=="in_progress"
 saved=client.patch(f"/api/patient-journeys/{item['id']}/encounter",headers=h,json={"anamnesis":"Sintetička anamneza","procedure_findings":"Sintetički nalaz","recommendations":"Plan prema odluci liječnika"});assert saved.status_code==200
 completed=client.post(f"/api/patient-journeys/{item['id']}/encounter/complete",headers=h);assert completed.status_code==200 and completed.json()["status"]=="completed"
 detail=client.get(f"/api/patient-journeys/{item['id']}",headers=h).json();assert detail["current_stage"]=="procedure_completed" and detail["encounter_status"]=="completed"
 assert client.patch(f"/api/patient-journeys/{item['id']}/encounter",headers=h,json={"diagnosis":"Naknadna izmjena"}).status_code==409
def test_empty_encounter_cannot_be_completed(client,db,auth_setup):
 item,h=journey(client,db);client.post(f"/api/patient-journeys/{item['id']}/encounter",headers=h);assert client.post(f"/api/patient-journeys/{item['id']}/encounter/complete",headers=h).status_code==422
