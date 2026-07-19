from app.core.security import hash_password
from app.models.domain import AuditLog, JourneyBlocker, Permission, Role, User
from tests.conftest import login_token
from tests.factories import appointment

def admin_headers(client): return {"Authorization":f"Bearer {login_token(client,'admin@test.local')}"}

def ready_journey(client,db):
    appt=appointment(db);headers=admin_headers(client)
    journey=client.post("/api/patient-journeys",headers=headers,json={"appointment_id":appt.id,"intake_channel":"manual","initial_stage":"booked"}).json()
    response=client.post(f"/api/patient-journeys/{journey['id']}/transition",headers=headers,json={"target_stage":"ready_for_arrival"});assert response.status_code==200
    return journey,headers

def reception_headers(client,db):
    permissions=db.query(Permission).filter(Permission.name.in_(["journey.read","checkin.update"])).all();role=Role(name="synthetic_reception",description="Synthetic",permissions=permissions);user=User(email="reception@test.local",full_name="Synthetic Reception",password_hash=hash_password("secret"),role=role);db.add(user);db.flush();return {"Authorization":f"Bearer {login_token(client,'reception@test.local')}"}

def test_start_check_in_records_arrival_and_structured_items(client,db,auth_setup):
    journey,headers=ready_journey(client,db)
    dashboard=client.get("/api/dashboard/day?selected_date=2026-07-06",headers=headers).json()
    row=next(item for item in dashboard["rows"] if item["journey_id"]==journey["id"])
    assert row["allowed_actions"]==["open_check_in"]
    response=client.post(f"/api/patient-journeys/{journey['id']}/check-in",headers=headers)
    assert response.status_code==200;body=response.json();assert body["status"]=="in_review" and body["arrived_at"]
    assert {item["category"] for item in body["items"]}=={"identity","preparation","preconditions"}
    assert "patient_data_confirmed" in {item["item_key"] for item in body["items"]}
    assert "last_food_drink" in {item["item_key"] for item in body["items"]}
    detail=client.get(f"/api/patient-journeys/{journey['id']}",headers=headers).json();assert detail["current_stage"]=="check_in_review" and detail["check_in_status"]=="in_review"

def test_reception_records_or_escalates_clinical_questions(client,db,auth_setup):
    journey,admin=ready_journey(client,db);checkin=client.post(f"/api/patient-journeys/{journey['id']}/check-in",headers=admin).json();clinical=next(item for item in checkin["items"] if item["item_key"]=="anticoagulants_antiplatelets");reception=reception_headers(client,db)
    recorded=client.patch(f"/api/patient-journeys/{journey['id']}/check-in/items/{clinical['id']}",headers=reception,json={"state":"confirmed","note":"Pacijent negira lijekove za razrjeđivanje krvi"});assert recorded.status_code==200
    escalated=client.patch(f"/api/patient-journeys/{journey['id']}/check-in/items/{clinical['id']}",headers=reception,json={"state":"requires_clinician_review","note":"Potrebna odluka liječnika"});assert escalated.status_code==200
    assert db.query(JourneyBlocker).filter_by(journey_id=journey["id"],is_clinical=True,status="open").count()==1
    confirmed=client.patch(f"/api/patient-journeys/{journey['id']}/check-in/items/{clinical['id']}",headers=admin,json={"state":"confirmed","note":"Liječnik pregledao"});assert confirmed.status_code==200
    assert confirmed.json()["status"]=="in_review"
    assert db.query(JourneyBlocker).filter_by(journey_id=journey["id"],status="open").count()==1

def test_reception_confirms_administrative_items_with_one_audited_action(client,db,auth_setup):
    journey,admin=ready_journey(client,db);client.post(f"/api/patient-journeys/{journey['id']}/check-in",headers=admin);reception=reception_headers(client,db)
    response=client.post(f"/api/patient-journeys/{journey['id']}/check-in/confirm-administrative",headers=reception)
    assert response.status_code==200
    items=response.json()["items"]
    assert all(item["state"]=="confirmed" for item in items if item["category"]=="identity")
    assert all(item["state"]=="not_confirmed" for item in items if item["category"]!="identity")
    assert db.query(AuditLog).filter_by(entity_type="PatientJourney",entity_id=journey["id"],action="checkin_administrative_confirmed").count()==1

def test_check_in_becomes_ready_only_after_every_item_is_human_resolved(client,db,auth_setup):
    journey,headers=ready_journey(client,db);checkin=client.post(f"/api/patient-journeys/{journey['id']}/check-in",headers=headers).json()
    latest=None
    for item in checkin["items"]:
        latest=client.patch(f"/api/patient-journeys/{journey['id']}/check-in/items/{item['id']}",headers=headers,json={"state":"not_applicable"})
        assert latest.status_code==200
    assert latest.json()["status"]=="ready"
    detail=client.get(f"/api/patient-journeys/{journey['id']}",headers=headers).json();assert detail["current_stage"]=="ready_for_clinician" and detail["check_in_status"]=="ready"
