from tests.conftest import login_token
from tests.factories import appointment
from app.schemas.journey_encounter import DiagnosisSuggestionsOut
from datetime import datetime,timezone
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
 saved=client.patch(f"/api/patient-journeys/{item['id']}/encounter",headers=h,json={"anamnesis":"Sintetička anamneza","examination":"Uredan sintetički status","patient_findings":"Donesen sintetički laboratorijski nalaz","opinion":"Mišljenje liječnika","recommendations":"Plan prema odluci liječnika","diagnosis":"Z00.0 — Opći medicinski pregled"});assert saved.status_code==200
 assert saved.json()["patient_findings"]=="Donesen sintetički laboratorijski nalaz" and saved.json()["opinion"]=="Mišljenje liječnika"
 completed=client.post(f"/api/patient-journeys/{item['id']}/encounter/complete",headers=h);assert completed.status_code==200 and completed.json()["status"]=="completed"
 detail=client.get(f"/api/patient-journeys/{item['id']}",headers=h).json();assert detail["current_stage"]=="procedure_completed" and detail["encounter_status"]=="completed"
 assert client.patch(f"/api/patient-journeys/{item['id']}/encounter",headers=h,json={"diagnosis":"Naknadna izmjena"}).status_code==409
def test_empty_encounter_cannot_be_completed(client,db,auth_setup):
 item,h=journey(client,db);client.post(f"/api/patient-journeys/{item['id']}/encounter",headers=h);assert client.post(f"/api/patient-journeys/{item['id']}/encounter/complete",headers=h).status_code==422
def test_ai_diagnosis_suggestions_are_explicit_and_not_saved_automatically(client,db,auth_setup,monkeypatch):
 item,h=journey(client,db);client.post(f"/api/patient-journeys/{item['id']}/encounter",headers=h)
 monkeypatch.setattr("app.api.routes.journey_encounter.suggest_icd10_diagnoses",lambda payload:DiagnosisSuggestionsOut(diagnoses=[{"code":"K21.9","title":"Gastroezofagealna refluksna bolest"}],model="test-model",generated_at=datetime.now(timezone.utc)))
 response=client.post(f"/api/patient-journeys/{item['id']}/encounter/diagnosis-suggestions",headers=h,json={"anamnesis":"Sintetičke tegobe"})
 assert response.status_code==200 and response.json()["diagnoses"][0]["code"]=="K21.9" and response.json()["provider"]=="openai"
 assert client.get(f"/api/patient-journeys/{item['id']}/encounter",headers=h).json()["diagnosis"] is None
