from app.models.domain import AuditLog
from tests.conftest import login_token
def headers(client): return {"Authorization":f"Bearer {login_token(client,'admin@test.local')}"}
def test_knowledge_protocol_review_lifecycle(client,db,auth_setup):
    created=client.post("/api/knowledge-protocols",headers=headers(client),json={"key":"demo-protocol","title":"Demo protokol","specialty":"general","version":"1.0","summary":"Samo sintetski referentni sadržaj.","source_title":"Provjerljivi izvor","source_url":"https://example.org/guideline","rules":[{"label":"Ljudski pregled","condition_text":"Kada liječnik procijeni da je relevantno.","guidance_text":"Otvoriti izvor i primijeniti stručnu prosudbu."}]})
    assert created.status_code==200 and created.json()["status"]=="draft"
    reviewed=client.post(f"/api/knowledge-protocols/{created.json()['id']}/review",headers=headers(client))
    assert reviewed.status_code==200 and reviewed.json()["status"]=="reviewed"
    archived=client.post(f"/api/knowledge-protocols/{created.json()['id']}/archive",headers=headers(client))
    assert archived.status_code==200 and archived.json()["status"]=="archived"
    assert {"create","review","archive"}.issubset({x.action for x in db.query(AuditLog).filter(AuditLog.entity_type=="KnowledgeProtocol")})
