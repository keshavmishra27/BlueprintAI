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

# Setup an in-memory SQLite database for testing
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

# We override the ProductService dependency to inject the deterministic parser
def override_get_product_service(db=Depends(override_get_db)):
    # Create the ProductService, but we need to ensure the deterministic parser is used
    service = ProductService(db)
    
    # We patch the analyze_idea method so that it uses the DeterministicIdeaParser
    original_analyze = service.analyze_idea
    def mock_analyze(idea, context=None):
        return original_analyze(idea, context, parser=DeterministicIdeaParser())
        
    service.analyze_idea = mock_analyze
    return service

# app.dependency_overrides[get_db] = override_get_db
# Actually we can just override get_product_service directly:
from product.api.v1.routes import get_product_service
app.dependency_overrides[get_product_service] = override_get_product_service

client = TestClient(app)

def test_decision_persistence_flow_invariant():
    """
    Must verify invariant:
    POST /ideas/analyze -> decision_id = X -> persist DecisionRecord(X) -> GET /decisions -> must contain X
    Compare: decision_id, idea identity, governance action, severity, components/architecture
    """
    # 1. POST /ideas/analyze
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
    
    # Since we used the deterministic parser and "UNRESOLVED" is in the idea text:
    # Wait, the parser returns "UNRESOLVED" for Cand_B, which should be the winning path if "unresolved" is in idea text.
    # We need to verify what the actual mock governance output maps to.
    
    # 2. GET /decisions and verify X is present
    get_response = client.get(f"/api/v1/decisions/{decision_id}")
    assert get_response.status_code == 200, get_response.text
    fetched_data = get_response.json()
    
    # 3. Compare at minimum all required fields
    assert fetched_data["id"] == decision_id
    # Idea identity is stored in decision_fingerprint (which hashes idea text and arch)
    assert fetched_data["decision_fingerprint"] == decision_data["decision_fingerprint"]
    assert fetched_data["governance"]["action"] == gov_action
    assert fetched_data["governance"]["severity"] == decision_data["governance"]["severity"]
    
    # Architecture components must match
    assert fetched_data["architecture"]["components"] == decision_data["architecture"]["components"]
    
    # Also verify it appears in the recent decisions list
    list_response = client.get("/api/v1/decisions")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert any(d["id"] == decision_id for d in list_data)

def test_journey_flow_to_decision():
    """
    Tests the End-to-End flow of starting a journey and completing it,
    which should automatically delegate to ProductService and generate a DecisionRecord.
    """
    # 1. Start journey with no uncertainties -> should complete immediately
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
    
    # 2. Verify the decision exists in canonical storage
    decision_id = data["decision_id"]
    get_resp = client.get(f"/api/v1/decisions/{decision_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == decision_id
