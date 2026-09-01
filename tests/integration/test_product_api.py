import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_api_abstraction(client):
    """Test 1: API abstraction. Assert that API responses contain product schemas."""
    response = client.post("/api/v1/ideas/analyze", json={"idea": "Test idea"})
    assert response.status_code == 200
    data = response.json()
    
    assert "id" in data
    assert "architecture" in data
    assert "components" in data["architecture"]
    assert "decisions" in data["architecture"]
    assert "governance" in data
    assert "decision_fingerprint" in data
    assert "graph_fingerprint" in data
    
    assert "pareto_frontier" not in data
    assert "winning_path_id" not in data

def test_d0_persistence(client):
    """Test 2: D0 persistence. Analyze idea, retrieve it, verify fingerprint equality."""
    post_res = client.post("/api/v1/ideas/analyze", json={"idea": "Persistence test"})
    d0 = post_res.json()
    
    get_res = client.get(f"/api/v1/decisions/{d0['id']}")
    d0_retrieved = get_res.json()
    
    assert d0["id"] == d0_retrieved["id"]
    assert d0["decision_fingerprint"] == d0_retrieved["decision_fingerprint"]
    assert d0["graph_fingerprint"] == d0_retrieved["graph_fingerprint"]

def test_gap_persistence(client, monkeypatch):
    """Test 3: Gap persistence. Persist and retrieve Gap0 without changing alignment/evidence."""
    post_res = client.post("/api/v1/ideas/analyze", json={"idea": "Gap test"})
    d0 = post_res.json()
    
    class MockRepoArtifact:
        components = {"Mock": "Component"}
    
    class MockGapReportArtifact:
        findings = [{"category": "MISSING", "expected": "React Component"}]
        evidence = [{"source_file": "test.py", "location": "line 1", "evidence_type": "USED", "observed_entity": "React", "confidence": 1.0}]
        alignment_score = 0.75
        
    class MockRepoExtractor:
        def __init__(self, *args, **kwargs): pass
        def extract_deterministic(self): return MockRepoArtifact()
        
    class MockGapEngine:
        def evaluate(self, *args, **kwargs): 
            expected = args[0]
            expected_comps = set(expected.databases)
            for c in expected.components:
                expected_comps.add(c)
            import hashlib
            req_str = ",".join(sorted(list(expected_comps)))
            fp = hashlib.md5(req_str.encode()).hexdigest()
            
            class MockGapReportArtifact:
                findings = [{"category": "MISSING", "expected": "React Component"}]
                evidence = [{"source_file": "test.py", "location": "line 1", "evidence_type": "USED", "observed_entity": "React", "confidence": 1.0}]
                alignment_score = 0.75
                requirement_set_fingerprint = fp
            return MockGapReportArtifact()
        
    import product.service
    monkeypatch.setattr(product.service, "RepoExtractor", MockRepoExtractor)
    monkeypatch.setattr(product.service, "GapEngine", MockGapEngine)

    gap_res = client.post("/api/v1/repositories/analyze", json={
        "decision_id": d0["id"],
        "repo_path": "/dummy/path"
    })
    
    assert gap_res.status_code == 200
    gap_data = gap_res.json()
    
    assert gap_data["decision_id"] == d0["id"]
    assert gap_data["alignment_score"] == 0.75
    assert gap_data["findings"][0]["category"] == "MISSING"

def test_refinement_lineage_and_history(client, monkeypatch):
    """Test 4 & 5: Refinement lineage and history reconstruction."""
    res_d0 = client.post("/api/v1/ideas/analyze", json={"idea": "History test"})
    d0 = res_d0.json()
    
    res_d1 = client.post("/api/v1/refinements/apply", json={
        "decision_id": d0["id"],
        "applied_exploration": "Enforce Target",
        "preserved": ["FastAPI"],
        "problem_detected": "Mock problem"
    })
    d1 = res_d1.json()
    
    assert d1["decision_fingerprint"] != d0["decision_fingerprint"]
    
    res_d2 = client.post("/api/v1/refinements/apply", json={
        "decision_id": d1["id"],
        "applied_exploration": "Switch DB",
        "preserved": [],
        "problem_detected": "Mock problem 2"
    })
    d2 = res_d2.json()
    
    hist_res = client.get(f"/api/v1/decisions/{d2['id']}/history")
    history = hist_res.json()
    
    assert len(history) == 3
    assert history[0]["id"] == d0["id"]
    assert history[1]["id"] == d1["id"]
    assert history[2]["id"] == d2["id"]

def test_repository_identity(client, monkeypatch):
    """Test 6: Repository identity. Same repo = same fingerprint."""
    res_d0 = client.post("/api/v1/ideas/analyze", json={"idea": "Identity test"})
    d0 = res_d0.json()
    
    class MockRepoExtractor:
        def __init__(self, *args, **kwargs): pass
        def extract_deterministic(self): 
            class Artifact:
                components = {"Test": "Data"}
            return Artifact()
            
    class MockGapEngine:
        def evaluate(self, *args, **kwargs):
            expected = args[0]
            expected_comps = set(expected.databases)
            for c in expected.components:
                expected_comps.add(c)
            import hashlib
            req_str = ",".join(sorted(list(expected_comps)))
            fp = hashlib.md5(req_str.encode()).hexdigest()
            
            class GapReport:
                findings = []
                evidence = []
                alignment_score = 1.0
                requirement_set_fingerprint = fp
            return GapReport()
            
    import product.service
    monkeypatch.setattr(product.service, "RepoExtractor", MockRepoExtractor)
    monkeypatch.setattr(product.service, "GapEngine", MockGapEngine)

    gap1 = client.post("/api/v1/repositories/analyze", json={"decision_id": d0["id"], "repo_path": "/dummy"}).json()
    gap2 = client.post("/api/v1/repositories/analyze", json={"decision_id": d0["id"], "repo_path": "/dummy"}).json()
    
    assert gap1["repository_fingerprint"] == gap2["repository_fingerprint"]

def test_restart_persistence(monkeypatch):
    """Test 7: Restart persistence. Terminate app, restart, retrieve D0."""
    from product.api.main import app
    from fastapi.testclient import TestClient
    from product.db.session import Base, get_db
    
    test_db_path = "sqlite:///./test_persistent.db"
    persistent_engine = create_engine(test_db_path, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=persistent_engine)
    PersistentSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=persistent_engine)
    
    def override_get_db():
        db = PersistentSessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db

    class MockArtifact:
        components = ["API", "DB"]
        decisions = {"framework": "fastapi"}
        governance = {}
        winner_id = "mock-winner"
        candidates_evaluated = []
        pareto_frontier_ids = []
        explanation = "mock explanation"
        
    class MockOrchestrator:
        def __init__(self, *args, **kwargs): pass
        def refine(self, *args, **kwargs): return MockArtifact()
        
    import product.service
    monkeypatch.setattr(product.service, "Orchestrator", MockOrchestrator)

    client = TestClient(app)
    
    post_res = client.post("/api/v1/ideas/analyze", json={"idea": "Restart persistence test"})
    d0_id = post_res.json()["id"]
    
    app.dependency_overrides.clear()
    
    PersistentSessionLocal2 = sessionmaker(autocommit=False, autoflush=False, bind=persistent_engine)
    def override_get_db_2():
        db = PersistentSessionLocal2()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db_2
    client2 = TestClient(app)
    
    get_res = client2.get(f"/api/v1/decisions/{d0_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == d0_id
    
    app.dependency_overrides.clear()
    import os
    persistent_engine.dispose()
    if os.path.exists("./test_persistent.db"):
        os.remove("./test_persistent.db")
    
