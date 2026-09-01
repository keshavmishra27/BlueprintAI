import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from product.api.v1.routes import router
from product.db.session import Base
from product.service import ProductService
from product.db.models import DecisionRecord

from fastapi import FastAPI
from sqlalchemy.pool import StaticPool

app = FastAPI()
app.include_router(router, prefix="/api/v1")

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

from product.api.v1.routes import get_db
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_m8_6_lifecycle_and_fingerprint_guard():
    resp = client.post("/api/v1/ideas/analyze", json={
        "idea": "A simple FastAPI service with Postgres",
        "context": {}
    })
    assert resp.status_code == 200
    root_decision = resp.json()
    root_id = root_decision["id"]
    
    assert root_decision["status"] == "ACTIVE"
    assert "requirement_set_fingerprint" in root_decision
    assert root_decision["requirement_set_fingerprint"] != ""
    
    resp_b = client.post("/api/v1/refinements/apply", json={
        "decision_id": root_id,
        "applied_exploration": "Use Redis for caching",
        "preserved": [],
        "problem_detected": "Performance"
    })
    assert resp_b.status_code == 200
    branch_b = resp_b.json()
    assert branch_b["status"] == "ACTIVE"
    b_id = branch_b["id"]
    
    resp_c = client.post("/api/v1/refinements/apply", json={
        "decision_id": root_id,
        "applied_exploration": "Use Memcached for caching",
        "preserved": [],
        "problem_detected": "Performance"
    })
    assert resp_c.status_code == 200
    branch_c = resp_c.json()
    assert branch_c["status"] == "ACTIVE"
    c_id = branch_c["id"]
    
    resp_a = client.get(f"/api/v1/decisions/{root_id}")
    assert resp_a.json()["status"] == "ACTIVE"
    
    resp_discovery = client.get(f"/api/v1/decisions?root_decision_id={root_id}&status=ACTIVE")
    assert resp_discovery.status_code == 200
    active_decisions = resp_discovery.json()
    assert len(active_decisions) == 3
    
    resp_patch = client.patch(f"/api/v1/decisions/{root_id}/status", json={"status": "SUPERSEDED"})
    assert resp_patch.status_code == 200
    assert resp_patch.json()["status"] == "SUPERSEDED"
    
    resp_discovery_2 = client.get(f"/api/v1/decisions?root_decision_id={root_id}&status=ACTIVE")
    assert len(resp_discovery_2.json()) == 2
    
    client.patch(f"/api/v1/decisions/{c_id}/status", json={"status": "REVOKED"})
    resp_discovery_3 = client.get(f"/api/v1/decisions?root_decision_id={root_id}&status=ACTIVE")
    assert len(resp_discovery_3.json()) == 1
    assert resp_discovery_3.json()[0]["id"] == b_id
    
    resp_lineage = client.get(f"/api/v1/decisions/{b_id}/lineage")
    assert resp_lineage.status_code == 200
    assert len(resp_lineage.json()) == 2
    
    resp_children = client.get(f"/api/v1/decisions/{root_id}/children")
    assert resp_children.status_code == 200
    assert len(resp_children.json()) == 2
    
    resp_eval_a = client.post("/api/v1/repositories/analyze", json={
        "decision_id": root_id,
        "repo_path": "./dummy_path"
    })
    assert resp_eval_a.status_code == 400
    assert "Cannot evaluate a non-ACTIVE decision" in resp_eval_a.json()["detail"]
    
    resp_eval_c = client.post("/api/v1/repositories/analyze", json={
        "decision_id": c_id,
        "repo_path": "./dummy_path"
    })
    assert resp_eval_c.status_code == 400
    assert "Cannot evaluate a non-ACTIVE decision" in resp_eval_c.json()["detail"]
    
    db = TestingSessionLocal()
    try:
        record_b = db.query(DecisionRecord).filter(DecisionRecord.id == b_id).first()
        db.execute(
            DecisionRecord.__table__.update().
            where(DecisionRecord.id == b_id).
            values(requirement_set_fingerprint="tampered_fingerprint_123")
        )
        db.commit()
    finally:
        db.close()
        
    resp_eval_tampered = client.post("/api/v1/repositories/analyze", json={
        "decision_id": b_id,
        "repo_path": "./dummy_path"
    })
    assert resp_eval_tampered.status_code == 400
    assert "Provenance violation" in resp_eval_tampered.json()["detail"]
    assert "Stored requirement fingerprint (tampered_fingerprint_123)" in resp_eval_tampered.json()["detail"]
