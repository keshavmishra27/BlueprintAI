import sys
import os
import json
from pydantic import BaseModel, ValidationError
from typing import List

# Mock the Pydantic models from repo_judge.py
class Improvement(BaseModel):
    file: str
    issue: str
    fix: str

class JudgeResult(BaseModel):
    student_name: str
    repository: str
    overall_score: int = 0
    code_quality_score: int = 0
    innovation_score: int = 0
    completeness_score: int = 0
    documentation_score: int = 0
    verdict: str = ""
    hackathon_readiness: str = ""
    strengths: List[str] = []
    improvements: List[Improvement] = []
    standout_files: List[str] = []
    problem_areas: List[str] = []

# This is what github_judge_service.py now returns on error
error_result = {
    "overall_score": 0,
    "code_quality_score": 0,
    "innovation_score": 0,
    "completeness_score": 0,
    "documentation_score": 0,
    "verdict": "Could not parse LLM response.",
    "hackathon_readiness": "No response from LLM.",
    "strengths": ["None identified due to processing error."],
    "improvements": [
        {
            "file": "General",
            "issue": "The AI returned an unparseable response.",
            "fix": "Please try again or check if the repository is too large."
        }
    ],
    "standout_files": [],
    "problem_areas": ["Processing failed."],
    "repository": "https://github.com/test/repo",
    "student_name": "Test Student",
}

print("Attempting to validate new error_result with JudgeResult model...")
try:
    JudgeResult(**error_result)
    print("Validation successful!")
except ValidationError as e:
    print(f"Validation failed: {e}")
