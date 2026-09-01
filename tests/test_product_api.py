import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from product.api.v1.models import Decision, GapReport
from unittest.mock import patch, MagicMock

client = TestClient(app)

@patch("product.api.v1.routes.ProductService")
def test_ideas_analyze_contract(MockService):
    mock_service_instance = MockService.return_value
    
    mock_decision = Decision(
        id="test-123",
        version=1,
        architecture={
            "components": [{"name": "React", "type": "frontend"}],
            "decisions": []
        },
        governance={
            "action": "Proceed",
            "severity": "Low"
        },
        alternatives=[],
        alignment=0.9,
        decision_fingerprint="abc",
        graph_fingerprint="def",
        context_fingerprint="ghi",
        requirement_set_fingerprint="req-abc",
        status="ACTIVE",
        created_at="2026-08-23T12:00:00Z"
    )
    mock_service_instance.analyze_idea.return_value = mock_decision

    response = client.post("/api/v1/ideas/analyze", json={
        "idea": "test idea",
        "context": {}
    })
    
    assert response.status_code == 200
    
    data = response.json()
    validated = Decision(**data)
    assert validated.id == "test-123"

@patch("product.api.v1.routes.ProductService")
def test_repositories_analyze_contract(MockService):
    mock_service_instance = MockService.return_value
    
    mock_gap_report = GapReport(
        id="gap-123",
        decision_id="test-123",
        decision_fingerprint="test-fingerprint",
        requirement_set_fingerprint="req-abc",
        repository_fingerprint="repo-abc",
        expected_architecture={
            "components": [{"name": "React", "type": "frontend"}],
            "decisions": []
        },
        actual_architecture={"components": ["React"]},
        findings=[],
        evidence=[],
        alignment_score=0.95,
        created_at="2026-08-23T12:05:00Z"
    )
    mock_service_instance.analyze_repository.return_value = mock_gap_report

    response = client.post("/api/v1/repositories/analyze", json={
        "decision_id": "test-123",
        "repo_path": "/some/path"
    })
    
    assert response.status_code == 200
    data = response.json()
    validated = GapReport(**data)
    assert validated.id == "gap-123"
