from datetime import date
from app.models.domain import AuditLog, Patient
from tests.conftest import login_token

def test_laboratory_order_results_flags_and_review(client, db, auth_setup):
    patient=Patient(first_name="Demo",last_name="Laboratorij",date_of_birth=date(1980,1,1)); db.add(patient); db.commit()
    headers={"Authorization":f"Bearer {login_token(client,'admin@test.local')}"}
    created=client.post("/api/laboratory/orders",headers=headers,json={"patient_id":patient.id,"ordered_at":"2026-07-12","external_laboratory":"Demo laboratorij","tests":[{"test_name":"CRP","unit":"mg/L","reference_low":0,"reference_high":5},{"test_name":"KKS"}]})
    assert created.status_code==200
    order=created.json(); ids=[item["id"] for item in order["results"]]
    collected=client.post(f"/api/laboratory/orders/{order['id']}/collect",headers=headers,json={"specimen_type":"blood"})
    assert collected.status_code==200 and collected.json()["collected_at"]
    saved=client.put(f"/api/laboratory/orders/{order['id']}/results",headers=headers,json={"collected":False,"results":[{"id":ids[0],"value":12,"unit":"mg/L","reference_low":0,"reference_high":5},{"id":ids[1],"text_value":"uredno"}]})
    assert saved.status_code==200 and saved.json()["status"]=="resulted"
    assert saved.json()["results"][0]["flag"]=="high"
    reviewed=client.post(f"/api/laboratory/orders/{order['id']}/review",headers=headers,json={"conclusion":"Nalaz pregledan; liječnik određuje daljnji postupak."})
    assert reviewed.status_code==200 and reviewed.json()["status"]=="reviewed"
    locked=client.put(f"/api/laboratory/orders/{order['id']}/results",headers=headers,json={"results":[{"id":ids[0],"value":4}]})
    assert locked.status_code==409
    history=client.get(f"/api/laboratory/patients/{patient.id}/history?test_name=CRP",headers=headers)
    assert history.status_code==200 and history.json()[0]["value"]=="12.0000"
    assert client.post(f"/api/laboratory/orders/{order['id']}/cancel",headers=headers,json={"reason":"Pogrešna narudžba"}).status_code==409
    second=client.post("/api/laboratory/orders",headers=headers,json={"patient_id":patient.id,"ordered_at":"2026-07-13","tests":[{"test_name":"TSH"}]}).json()
    cancelled=client.post(f"/api/laboratory/orders/{second['id']}/cancel",headers=headers,json={"reason":"Pogrešno odabran predložak"})
    assert cancelled.status_code==200 and cancelled.json()["status"]=="cancelled"
    actions={item.action for item in db.query(AuditLog).filter(AuditLog.entity_type=="LabOrder")}
    assert {"create","sample_collected","results_update","review","cancel"}.issubset(actions)

def test_laboratory_templates_are_available(client, auth_setup):
    headers={"Authorization":f"Bearer {login_token(client,'admin@test.local')}"}
    response=client.get("/api/laboratory/templates",headers=headers)
    assert response.status_code==200
