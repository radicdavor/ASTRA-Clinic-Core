from datetime import date
from app.models.domain import AuditLog, Patient
from tests.conftest import login_token

def test_therapy_lifecycle_is_patient_scoped_and_audited(client,db,auth_setup):
    patient=Patient(first_name="Demo",last_name="Terapija",date_of_birth=date(1985,2,3));db.add(patient);db.commit()
    headers={"Authorization":f"Bearer {login_token(client,'admin@test.local')}"}
    created=client.post("/api/therapies",headers=headers,json={"patient_id":patient.id,"name":"Demo terapija","instructions":"Jednom dnevno prema odluci liječnika","start_date":"2026-07-12","prescriber":"dr. Demo"})
    assert created.status_code==200 and created.json()["status"]=="active"
    therapy_id=created.json()["id"]
    listed=client.get(f"/api/therapies?patient_id={patient.id}",headers=headers)
    assert listed.status_code==200 and len(listed.json())==1
    updated=client.put(f"/api/therapies/{therapy_id}",headers=headers,json={"name":"Demo terapija","instructions":"Dvije doze prema odluci liječnika","start_date":"2026-07-12","end_date":"2026-08-12","prescriber":"dr. Demo"})
    assert updated.status_code==200 and updated.json()["instructions"].startswith("Dvije")
    stopped=client.post(f"/api/therapies/{therapy_id}/stop",headers=headers,json={"reason":"Odluka liječnika nakon kontrole"})
    assert stopped.status_code==200 and stopped.json()["status"]=="stopped"
    assert client.put(f"/api/therapies/{therapy_id}",headers=headers,json={"name":"XX","instructions":"Promjena","start_date":"2026-07-12"}).status_code==409
    actions={row.action for row in db.query(AuditLog).filter(AuditLog.entity_type=="Therapy")}
    assert {"create","update","stop"}.issubset(actions)

def test_therapy_can_be_completed_and_renewed_as_new_record(client,db,auth_setup):
    patient=Patient(first_name="Ana",last_name="Obnova",date_of_birth=date(1990,4,5));db.add(patient);db.commit()
    headers={"Authorization":f"Bearer {login_token(client,'admin@test.local')}"}
    source=client.post("/api/therapies",headers=headers,json={"patient_id":patient.id,"name":"Kontrolirana terapija","instructions":"Prema odluci liječnika","start_date":"2026-07-01"}).json()
    completed=client.post(f"/api/therapies/{source['id']}/complete",headers=headers,json={"note":"Provedeno prema planu"})
    assert completed.status_code==200 and completed.json()["status"]=="completed" and completed.json()["completion_note"]
    renewed=client.post(f"/api/therapies/{source['id']}/renew",headers=headers,json={"start_date":"2026-08-01","end_date":"2026-09-01"})
    assert renewed.status_code==200 and renewed.json()["parent_therapy_id"]==source["id"] and renewed.json()["status"]=="active"
    assert client.post(f"/api/therapies/{renewed.json()['id']}/renew",headers=headers,json={"start_date":"2026-10-01"}).status_code==409
