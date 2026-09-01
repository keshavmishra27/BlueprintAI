import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def generate_valid_payload():
    return {
        "decision_id": "mock-decision-123",
        "project_name": "TestProject",
        "repo_path": "d:/test/repo",
        "tech_stack": ["Python", "FastAPI"],
        "overall_confidence": "Medium",
        "overall_assessment": "Looks okay.",
        "checks": [],
        "limitations": [],
        "evidence": [
            {
                "id": "E-001",
                "description": "General architecture review.",
                "source_type": "workspace_inspection"
            }
        ],
        "categories": {
            "architecture": {
                "score": 90,
                "confidence": "High",
                "evidence_ids": ["E-001"],
                "explanation": "Good.",
                "highest_priority_improvement": "None"
            },
            "code_quality": {
                "score": 80,
                "confidence": "Medium",
                "evidence_ids": [],
                "explanation": "Good.",
                "highest_priority_improvement": "None"
            },
            "security": {
                "score": 100,
                "confidence": "High",
                "evidence_ids": [],
                "explanation": "Good.",
                "highest_priority_improvement": "None"
            },
            "testing_reliability": {
                "score": 50,
                "confidence": "Low",
                "evidence_ids": [],
                "explanation": "Needs tests.",
                "highest_priority_improvement": "Add tests"
            },
            "maintainability": {
                "score": 70,
                "confidence": "Medium",
                "evidence_ids": [],
                "explanation": "Good.",
                "highest_priority_improvement": "None"
            },
            "documentation_hygiene": {
                "score": 60,
                "confidence": "Medium",
                "evidence_ids": [],
                "explanation": "Good.",
                "highest_priority_improvement": "None"
            }
        },
        "findings": [
            {
                "id": "F-001",
                "title": "Need more tests",
                "severity": "Medium",
                "classification": "Recommendation",
                "category": "testing_reliability",
                "explanation": "Code lacks coverage.",
                "impact": "Bugs",
                "recommendation": "Add pytest.",
                "evidence_ids": ["E-001"]
            }
        ],
        "positive_decisions": [],
        "priorities": [
            {
                "priority_number": 1,
                "action": "Write tests",
                "reason": "Crucial",
                "related_finding_ids": ["F-001"]
            }
        ]
    }

import urllib.request
from unittest.mock import patch, MagicMock
import json

@pytest.fixture(autouse=True)
def mock_product_api():
    with patch('urllib.request.urlopen') as mock_urlopen:
        def side_effect(req, *args, **kwargs):
            mock_response = MagicMock()
            mock_response.status = 200
            url = req.full_url
            if url.endswith("/api/v1/repositories/analyze"):
                mock_response.read.return_value = json.dumps({
                    "decision_id": "mock-decision-123",
                    "decision_fingerprint": "mock-fingerprint-abc"
                }).encode('utf-8')
            else:
                mock_response.read.return_value = json.dumps({
                    "id": "mock-decision-123",
                    "decision_fingerprint": "mock-fingerprint-abc"
                }).encode('utf-8')
            mock_response.__enter__.return_value = mock_response
            return mock_response
            
        mock_urlopen.side_effect = side_effect
        yield mock_urlopen

def test_valid_payload_accepted():
    payload = generate_valid_payload()
    response = client.post("/api/analysis", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "analysis_id" in data["metadata"]
    assert data["metadata"]["schema_version"] == "1.0.0"

def test_overall_score_calculated_correctly():
    payload = generate_valid_payload()
    response = client.post("/api/analysis", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["semantic"]["report"]["overall"]["score"] == 80

def test_invalid_category_score_rejected():
    payload = generate_valid_payload()
    payload["categories"]["architecture"]["score"] = 150
    response = client.post("/api/analysis", json=payload)
    assert response.status_code == 422

def test_missing_evidence_reference_rejected():
    payload = generate_valid_payload()
    payload["findings"][0]["evidence_ids"].append("E-999")
    response = client.post("/api/analysis", json=payload)
    assert response.status_code == 422
    assert "references unknown evidence ID" in response.text

def test_duplicate_evidence_id_rejected():
    payload = generate_valid_payload()
    payload["evidence"].append(payload["evidence"][0])
    response = client.post("/api/analysis", json=payload)
    assert response.status_code == 422
    assert "Duplicate evidence IDs found" in response.text

def test_missing_related_finding_id_rejected():
    payload = generate_valid_payload()
    payload["priorities"][0]["related_finding_ids"].append("F-999")
    response = client.post("/api/analysis", json=payload)
    assert response.status_code == 422
    assert "references unknown finding ID" in response.text

def test_credential_leak_rejected_safely():
    payload = generate_valid_payload()
    payload["evidence"][0]["description"] = "Found key: sk-abcdefghijklmnopqrstuvwxyz1234567890abcdefghijkl"
    
    response = client.post("/api/analysis", json=payload)
    assert response.status_code == 400
    assert "Sensitive credential-like content was detected" in response.json()["detail"]
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in response.text

def test_store_and_retrieve_analysis():
    payload = generate_valid_payload()
    post_resp = client.post("/api/analysis", json=payload)
    assert post_resp.status_code == 200
    
    analysis_id = post_resp.json()["metadata"]["analysis_id"]
    
    get_resp = client.get(f"/api/analysis/{analysis_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["metadata"]["analysis_id"] == analysis_id

def test_unknown_analysis_returns_404():
    response = client.get("/api/analysis/fake-id")
    assert response.status_code == 404

def test_identity_propagation_boundary(mock_product_api):
    payload = generate_valid_payload()
    payload["decision_id"] = "test-decision-999"
    
    def side_effect(req, *args, **kwargs):
        mock_response = MagicMock()
        mock_response.status = 200
        url = req.full_url
        if url.endswith("/api/v1/repositories/analyze"):
            mock_response.read.return_value = json.dumps({
                "decision_id": "test-decision-999",
                "decision_fingerprint": "fingerprint-for-999"
            }).encode('utf-8')
        else:
            mock_response.read.return_value = json.dumps({
                "id": "test-decision-999",
                "decision_fingerprint": "fingerprint-for-999"
            }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        return mock_response
        
    mock_product_api.side_effect = side_effect

    response = client.post("/api/analysis", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["metadata"]["decision_id"] == "test-decision-999"
    assert data["metadata"]["decision_fingerprint"] == "fingerprint-for-999"

def test_decision_identity_mismatch_rejected(mock_product_api):
    payload = generate_valid_payload()
    
    def side_effect(req, *args, **kwargs):
        mock_response = MagicMock()
        mock_response.status = 200
        url = req.full_url
        if url.endswith("/api/v1/repositories/analyze"):
            mock_response.read.return_value = json.dumps({
                "decision_id": "different-decision",
                "decision_fingerprint": "mock-fingerprint-abc"
            }).encode('utf-8')
        else:
            mock_response.read.return_value = json.dumps({
                "id": "mock-decision-123",
                "decision_fingerprint": "mock-fingerprint-abc"
            }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        return mock_response
        
    mock_product_api.side_effect = side_effect
    
    response = client.post("/api/analysis", json=payload)
    assert response.status_code == 400
    assert "Decision ID mismatch" in response.json()["detail"]
