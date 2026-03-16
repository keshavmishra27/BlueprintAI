
import sys
import os
from pydantic import ValidationError

# Add backend to path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.routers.repo_judge import JudgeResult, SecurityWarning

def test_security_warning_mapping():
    print("Testing SecurityWarning mapping...")
    
    # Simulate the problematic data from the user's screenshot
    # 'title': 'Hardcoded API ...py', 'lines': '47-50'
    bad_data = {
        "title": "Hardcoded API Key",
        "lines": "47-50"
    }
    
    warning = SecurityWarning(**bad_data)
    print(f"Mapped Warning: {warning}")
    
    assert warning.type == "Hardcoded API Key"
    assert warning.evidence == "Lines 47-50"
    assert warning.remediation == "No remediation provided"
    print("PASSED: SecurityWarning mapping test!")

def test_full_result_validation():
    print("\nTesting full JudgeResult validation...")
    
    # Combined problematic data
    mock_result = {
        "repo_url": "https://github.com/test/repo",
        "accessibility": "public",
        "languages": ["python"],
        "scores": {
            "functionality": {"score": 8, "reasons": ["Works well"]},
            "code_quality": {"score": 7, "reasons": []},
            "documentation": {"score": 6, "reasons": []},
            "architecture": {"score": 7, "reasons": []},
            "testing_ci": {"score": 5, "reasons": []},
            "innovation_ux": {"score": 8, "reasons": []}
        },
        "total_score": 70,
        "strengths": ["Clean code"],
        "top_issues": [
            {
                "severity": "major",
                "title": "Slow Loop",
                "description": "Optimize the loop",
                "estimated_effort_hours": 1.0
            }
        ],
        "security_warnings": [
            {
                "title": "Exposure of Secret",
                "lines": "12-15"
            },
            {
                "type": "unsafe_eval",
                "evidence": "eval(input())",
                "remediation": "Don't use eval"
            }
        ],
        "reproducibility": {"can_run": True, "notes": "None"},
        "mentor_notes": "Good job."
    }
    
    try:
        validated = JudgeResult(**mock_result)
        print("PASSED: JudgeResult validation passed!")
        print(f"Validated security_warnings: {validated.security_warnings}")
    except ValidationError as e:
        print(f"FAILED: Validation failed: {e}")
        sys.exit(1)

def test_sparse_result_validation():
    print("\nTesting sparse JudgeResult validation (simulating incomplete AI response)...")
    
    # Missing many fields, but should be handled by defaults in JudgeResult
    sparse_result = {
        "repo_url": "https://github.com/test/sparse",
        "mentor_notes": "Sparse response test."
        # total_score, scores, reproducibility etc. are missing
    }
    
    try:
        # Note: In the live app, github_judge_service.py now catches missing 'total_score' 
        # and returns a fallback. But here we test that IF it reached the model, 
        # the model would still validate due to defaults.
        validated = JudgeResult(**sparse_result)
        print("PASSED: Sparse JudgeResult validation passed!")
        assert validated.total_score == 0.0
        assert validated.accessibility == "public"
        assert validated.scores.functionality.score == 0.0
    except ValidationError as e:
        print(f"FAILED: Sparse validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_security_warning_mapping()
    test_full_result_validation()
    test_sparse_result_validation()
