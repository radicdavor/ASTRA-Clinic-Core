from tests.conftest import login_token
from tests.factories import appointment
from app.schemas.journey_encounter import DiagnosisSuggestionsOut
from app.models.domain import AuditLog
from app.services.encounter_diagnosis import DiagnosisSuggestionUnavailable
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
 monkeypatch.setattr("app.api.routes.journey_encounter.ensure_diagnosis_suggestions_enabled",lambda:{"K21.9":"Gastroezofagealna refluksna bolest"})
 monkeypatch.setattr("app.api.routes.journey_encounter.suggest_icd10_diagnoses",lambda payload:DiagnosisSuggestionsOut(diagnoses=[{"code":"K21.9","title":"Gastroezofagealna refluksna bolest"}],model="test-model",generated_at=datetime.now(timezone.utc),request_id="synthetic-request"))
 response=client.post(f"/api/patient-journeys/{item['id']}/encounter/diagnosis-suggestions",headers=h,json={"anamnesis":"Sintetičke tegobe"})
 assert response.status_code==200 and response.json()["diagnoses"][0]["code"]=="K21.9" and response.json()["provider"]=="openai"
 assert client.get(f"/api/patient-journeys/{item['id']}/encounter",headers=h).json()["diagnosis"] is None

def test_ai_diagnosis_suggestions_fail_closed_when_disabled(client,db,auth_setup,monkeypatch):
 item,h=journey(client,db);client.post(f"/api/patient-journeys/{item['id']}/encounter",headers=h)
 def disabled(): raise DiagnosisSuggestionUnavailable("AI prijedlozi dijagnoza isključeni su u ovom okruženju.")
 monkeypatch.setattr("app.api.routes.journey_encounter.ensure_diagnosis_suggestions_enabled",disabled)
 response=client.post(f"/api/patient-journeys/{item['id']}/encounter/diagnosis-suggestions",headers=h,json={"anamnesis":"Sintetičke tegobe"})
 assert response.status_code==503 and "isključeni" in response.json()["detail"]

def test_ai_diagnosis_accept_and_reject_are_individual_and_audited(client,db,auth_setup,monkeypatch):
 item,h=journey(client,db);opened=client.post(f"/api/patient-journeys/{item['id']}/encounter",headers=h).json()
 monkeypatch.setattr("app.api.routes.journey_encounter.ensure_diagnosis_suggestions_enabled",lambda:{"K21.9":"Kanonski naziv"})
 payload={"code":"k21.9","title":"Generirani naziv","provider":"openai","model":"test-model","request_id":"synthetic-request"}
 accepted=client.post(f"/api/patient-journeys/{item['id']}/encounter/diagnosis-suggestions/decision",headers=h,json={**payload,"action":"accept"})
 rejected=client.post(f"/api/patient-journeys/{item['id']}/encounter/diagnosis-suggestions/decision",headers=h,json={**payload,"action":"reject"})
 assert accepted.status_code==200 and accepted.json()["diagnosis"]=="K21.9 — Kanonski naziv"
 assert rejected.status_code==200
 events=db.query(AuditLog).filter(AuditLog.entity_type=="JourneyEncounter",AuditLog.entity_id==opened["id"],AuditLog.action.in_(["ai_diagnosis_suggestion_accepted","ai_diagnosis_suggestion_rejected"])).all()
 assert {event.action for event in events}=={"ai_diagnosis_suggestion_accepted","ai_diagnosis_suggestion_rejected"}
 assert all("Sintetičke tegobe" not in str(event.after_json) for event in events)
 assert next(event for event in events if event.action=="ai_diagnosis_suggestion_accepted").after_json["final_code_added"]=="K21.9"

def test_ai_diagnosis_decision_rejects_unknown_catalog_code(client,db,auth_setup,monkeypatch):
 item,h=journey(client,db);client.post(f"/api/patient-journeys/{item['id']}/encounter",headers=h)
 monkeypatch.setattr("app.api.routes.journey_encounter.ensure_diagnosis_suggestions_enabled",lambda:{"K21.9":"Kanonski naziv"})
 response=client.post(f"/api/patient-journeys/{item['id']}/encounter/diagnosis-suggestions/decision",headers=h,json={"action":"accept","code":"X99.9","title":"Nepoznata","provider":"openai","model":"test-model","request_id":"synthetic-request"})
 assert response.status_code==422

def test_completed_encounter_and_wrong_role_cannot_request_ai_suggestions(client,db,auth_setup,monkeypatch):
 item,h=journey(client,db);client.post(f"/api/patient-journeys/{item['id']}/encounter",headers=h)
 client.patch(f"/api/patient-journeys/{item['id']}/encounter",headers=h,json={"anamnesis":"Sintetička anamneza"})
 client.post(f"/api/patient-journeys/{item['id']}/encounter/complete",headers=h)
 monkeypatch.setattr("app.api.routes.journey_encounter.ensure_diagnosis_suggestions_enabled",lambda:{"K21.9":"Kanonski naziv"})
 assert client.post(f"/api/patient-journeys/{item['id']}/encounter/diagnosis-suggestions",headers=h,json={"anamnesis":"Tekst"}).status_code==409
 limited={"Authorization":f"Bearer {login_token(client,'limited@test.local')}"}
 assert client.post(f"/api/patient-journeys/{item['id']}/encounter/diagnosis-suggestions",headers=limited,json={"anamnesis":"Tekst"}).status_code==403
