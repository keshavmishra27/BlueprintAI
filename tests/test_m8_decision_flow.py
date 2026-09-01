import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi import FastAPI, Depends
from product.api.v1.routes import router as product_router
from product.db.session import get_db
from product.db.models import Base
from product.service import ProductService
from idea_refiner.parsers.deterministic import DeterministicIdeaParser
from product.api.v1.models import Decision

app = FastAPI()
app.include_router(product_router, prefix="/api/v1")

from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

from fastapi import Depends

def override_get_product_service(db=Depends(override_get_db)):
    service = ProductService(db)
    
    original_analyze = service.analyze_idea
    def mock_analyze(idea, context=None):
        return original_analyze(idea, context, parser=DeterministicIdeaParser())
        
    service.analyze_idea = mock_analyze
    return service

from product.api.v1.routes import get_product_service
app.dependency_overrides[get_product_service] = override_get_product_service

client = TestClient(app)

def test_decision_persistence_flow_invariant():
    """
    Must verify invariant:
    POST /ideas/analyze -> decision_id = X -> persist DecisionRecord(X) -> GET /decisions -> must contain X
    Compare: decision_id, idea identity, governance action, severity, components/architecture
    """
    idea_text = "This idea will be UNRESOLVED"
    post_response = client.post("/api/v1/ideas/analyze", json={
        "idea": idea_text,
        "context": {}
    })
    
    assert post_response.status_code == 200, post_response.text
    decision_data = post_response.json()
    
    decision_id = decision_data["id"]
    assert decision_id is not None
    
    gov_action = decision_data["governance"]["action"]
    
    
    get_response = client.get(f"/api/v1/decisions/{decision_id}")
    assert get_response.status_code == 200, get_response.text
    fetched_data = get_response.json()
    
    assert fetched_data["id"] == decision_id
    assert fetched_data["decision_fingerprint"] == decision_data["decision_fingerprint"]
    assert fetched_data["governance"]["action"] == gov_action
    assert fetched_data["governance"]["severity"] == decision_data["governance"]["severity"]
    
    assert fetched_data["architecture"]["components"] == decision_data["architecture"]["components"]
    
    list_response = client.get("/api/v1/decisions")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert any(d["id"] == decision_id for d in list_data)

def test_journey_flow_to_decision():
    """
    Tests the End-to-End flow of starting a journey and completing it,
    which should automatically delegate to ProductService and generate a DecisionRecord.
    """
    start_payload = {
        "what": "A new platform",
        "why": "To test journey flow",
        "how": "Using microservices",
        "constraints": ["budget < 10k"],
        "requirements": [],
        "gemini_baseline_architecture": {
            "inputs": [],
            "processing": ["A"],
            "decision": [],
            "output": []
        },
        "player_b_architecture": {
            "inputs": [],
            "processing": ["B"],
            "decision": [],
            "output": []
        },
        "uncertainties": []
    }
    
    start_resp = client.post("/api/v1/journey/start", json=start_payload)
    assert start_resp.status_code == 200, start_resp.text
    data = start_resp.json()
    
    assert data["is_complete"] is True
    assert data["session_id"] is not None
    assert data["decision_id"] is not None
    assert data["decision_fingerprint"] is not None
    
    decision_id = data["decision_id"]
    get_resp = client.get(f"/api/v1/decisions/{decision_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == decision_id
