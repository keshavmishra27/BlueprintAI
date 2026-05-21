import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.routers.repo_judge import JudgeResult, SecurityWarning
from backend.app.services.github_judge_service import _adjust_simple_project_scores


def test_security_warning_mapping():
    bad_data = {"title": "Hardcoded API Key", "lines": "47-50"}
    warning = SecurityWarning(**bad_data)
    assert warning.type == "Hardcoded API Key"
    assert warning.evidence == "Lines 47-50"


def test_full_result_validation():
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
            "innovation_ux": {"score": 8, "reasons": []},
        },
        "total_score": 70,
        "strengths": ["Clean code"],
        "top_issues": [
            {
                "severity": "major",
                "title": "Slow Loop",
                "description": "Optimize the loop",
                "estimated_effort_hours": 1.0,
            }
        ],
        "security_warnings": [
            {"title": "Exposure of Secret", "lines": "12-15"},
            {
                "type": "unsafe_eval",
                "evidence": "eval(input())",
                "remediation": "Don't use eval",
            },
        ],
        "reproducibility": {"can_run": True, "notes": "None"},
        "mentor_notes": "Good job.",
    }
    validated = JudgeResult(**mock_result)
    assert validated.total_score == 70.5
    assert len(validated.security_warnings) == 2


def test_simple_project_score_caps():
    result = {
        "repo_url": "https://github.com/test/simple",
        "scores": {
            "functionality": {"score": 7, "reasons": ["Core feature works"]},
            "code_quality": {"score": 5, "reasons": ["Acceptable style"]},
            "documentation": {"score": 6, "reasons": ["Basic README"]},
            "architecture": {"score": 7, "reasons": ["Single-purpose script"]},
            "testing_ci": {"score": 5, "reasons": ["No tests present"]},
            "innovation_ux": {"score": 8, "reasons": ["Simple model classifier"]},
        },
        "total_score": 52,
        "mentor_notes": "Initial assessment.",
    }
    adjusted = _adjust_simple_project_scores(result, {"likely_tutorial": True})
    assert adjusted["scores"]["architecture"]["score"] == 3.0
    assert adjusted["scores"]["testing_ci"]["score"] == 1.0
    assert adjusted["scores"]["innovation_ux"]["score"] == 2.0
    assert adjusted["total_score"] <= 45
    assert "small tutorial/miniproject" in adjusted["mentor_notes"].lower()


def test_sparse_result_validation():
    sparse_result = {
        "repo_url": "https://github.com/test/sparse",
        "mentor_notes": "Sparse response test.",
    }
    validated = JudgeResult(**sparse_result)
    assert validated.total_score == 0.0
    assert validated.scores.functionality.score == 0.0
