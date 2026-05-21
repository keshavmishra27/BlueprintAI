import os
import logging
from typing import List, Optional
import requests as http_requests
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, ValidationError, model_validator
from typing import List, Optional
from backend.app.database import get_db
from backend.app.middleware.rate_limit import limiter
from backend.app.models import RepoAnalysis

router = APIRouter(prefix="/repo-judge", tags=["Repo Judge"])
logger = logging.getLogger(__name__)

# ── Strict JSON schema example for LLM prompts ─────────────────────────
# Imported by repo_crew.py and github_judge_service.py so every call site
# shows the LLM the exact same contract.
JUDGE_JSON_SCHEMA = """\
{
  "repo_url": "<github_url>",
  "accessibility": "public",
  "languages": ["Python", "JavaScript"],
  "scores": {
    "functionality": {"score": 7.0, "weight": 0.25, "reasons": ["reason 1", "reason 2"]},
    "code_quality":  {"score": 6.0, "weight": 0.20, "reasons": ["reason 1"]},
    "documentation": {"score": 5.0, "weight": 0.15, "reasons": ["reason 1"]},
    "architecture":  {"score": 7.0, "weight": 0.15, "reasons": ["reason 1"]},
    "testing_ci":    {"score": 3.0, "weight": 0.10, "reasons": ["reason 1"]},
    "innovation_ux": {"score": 6.0, "weight": 0.15, "reasons": ["reason 1"]}
  },
  "total_score": 56.5,
  "strengths": ["strength 1", "strength 2"],
  "top_issues": [
    {
      "severity": "major",
      "title": "Issue title",
      "description": "Detailed description",
      "files": [{"path": "src/app.py", "lines": "10-25", "excerpt": "optional code snippet"}],
      "estimated_effort_hours": 2.0
    }
  ],
  "suggested_github_issues": [
    {"title": "Issue title", "body": "Issue body markdown", "labels": ["bug", "priority"]}
  ],
  "security_warnings": [
    {"type": "hardcoded_secret", "evidence": "API key in config.py line 5", "remediation": "Use env vars"}
  ],
  "reproducibility": {
    "can_run": true,
    "run_commands": ["pip install -r requirements.txt", "python main.py"],
    "notes": "Runs after installing dependencies"
  },
  "recommended_tests": [
    {"name": "test_login", "description": "Test user login flow", "file": "tests/test_auth.py"}
  ],
  "mentor_notes": "Overall feedback paragraph as a single string.",
  "coding_style_summary": "Paragraph about naming, modularity, consistency."
}"""
from ..services.llm_factory import check_llm_availability
class AnalyzeRequest(BaseModel):
    github_url: str
    student_name: str = "Anonymous"
class ScoreDetail(BaseModel):
    score: float = 0.0
    weight: Optional[float] = 0.0
    reasons: List[str] = []
    @model_validator(mode='before')
    @classmethod
    def coerce_primitive(cls, data):
        # LLM sometimes returns just a number e.g. 7
        if isinstance(data, (int, float)):
            return {"score": float(data)}
        # LLM sometimes returns reasons as a single string
        if isinstance(data, dict):
            reasons = data.get('reasons')
            if isinstance(reasons, str):
                data['reasons'] = [reasons]
        return data
class Scores(BaseModel):
    functionality: ScoreDetail = ScoreDetail()
    code_quality: ScoreDetail = ScoreDetail()
    documentation: ScoreDetail = ScoreDetail()
    architecture: ScoreDetail = ScoreDetail()
    testing_ci: ScoreDetail = ScoreDetail()
    innovation_ux: ScoreDetail = ScoreDetail()
class IssueFile(BaseModel):
    path: str
    lines: str = ""
    excerpt: Optional[str] = None
    @model_validator(mode='before')
    @classmethod
    def coerce_string_to_issue_file(cls, data):
        if isinstance(data, str):
            return {"path": data, "lines": ""}
        return data
class TopIssue(BaseModel):
    severity: str = "major"
    title: str = "Issue"
    description: str = "No description available"
    files: List[IssueFile] = []
    estimated_effort_hours: Optional[float] = 0.0
    @model_validator(mode='before')
    @classmethod
    def handle_string_input(cls, data):
        if isinstance(data, str):
            return {
                "title": "Concern",
                "description": data,
                "severity": "major"
            }
        return data
class GithubIssueTemplate(BaseModel):
    title: str
    body: str
    labels: List[str]
class SecurityWarning(BaseModel):
    type: Optional[str] = "unknown"
    evidence: Optional[str] = "Not specified"
    remediation: Optional[str] = "No remediation provided"
    @model_validator(mode='before')
    @classmethod
    def map_fields(cls, data):
        if isinstance(data, str):
            return {
                "type": "security_concern",
                "evidence": data,
                "remediation": "Review the flagged code for security implications."
            }
        if isinstance(data, dict):
            if 'title' in data and not data.get('type'):
                data['type'] = data['title']
            if not data.get('evidence'):
                if 'lines' in data:
                    data['evidence'] = f"Lines {data['lines']}"
                elif 'description' in data:
                    data['evidence'] = data['description']
        return data
class Reproducibility(BaseModel):
    can_run: bool = False
    run_commands: List[str] = []
    notes: str = ""
    @model_validator(mode='before')
    @classmethod
    def coerce_string(cls, data):
        # LLM sometimes returns a plain string description
        if isinstance(data, str):
            return {"notes": data, "can_run": False}
        return data
class RecommendedTest(BaseModel):
    name: str
    description: str
    file: str
class JudgeResult(BaseModel):
    repo_url: str
    accessibility: str = "public"
    languages: List[str] = []
    scores: Scores = Scores()
    total_score: float = 0.0
    strengths: List[str] = []
    top_issues: List[TopIssue] = []
    suggested_github_issues: List[GithubIssueTemplate] = []
    security_warnings: List[SecurityWarning] = []
    reproducibility: Reproducibility = Reproducibility()
    recommended_tests: List[RecommendedTest] = []
    mentor_notes: str = "Analysis completed."
    student_name: Optional[str] = None
    @model_validator(mode='before')
    @classmethod
    def coerce_fields(cls, data):
        if isinstance(data, dict):
            # accessibility: dict -> str
            acc = data.get('accessibility')
            if isinstance(acc, dict):
                data['accessibility'] = (
                    acc.get('rating') or acc.get('description') or 'public'
                )
            # mentor_notes: list -> newline-joined str
            notes = data.get('mentor_notes')
            if isinstance(notes, list):
                data['mentor_notes'] = '\n'.join(str(n) for n in notes)
            elif notes is not None and not isinstance(notes, str):
                data['mentor_notes'] = str(notes)
        return data
@router.get(
    "/health",
    summary="Repo Judge health check",
)
def health():
    return {"status": "ok", "route": "/repo-judge"}
@router.post(
    "/analyze",
    summary="Analyze a public GitHub repo (static analysis + CrewAI judges)",
    description=(
        "Downloads the repository archive, runs ruff/bandit when installed, "
        "then CrewAI agents (code analyst, security reviewer, mentor) return JSON. "
        "Static-only — code is not executed."
    ),
)
@limiter.limit("5/minute")
def analyze_repo(
    request: Request,
    req: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    if not req.github_url.strip():
        raise HTTPException(status_code=400, detail="github_url cannot be empty.")
    if not req.student_name.strip():
        raise HTTPException(status_code=400, detail="student_name cannot be empty.")
    check_llm_availability()
    from ..services.github_judge_service import analyze_repo as run_analysis
    try:
        result = run_analysis(
            github_url=req.github_url.strip(),
            student_name=req.student_name.strip(),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {e}",
        )
    import copy
    persisted = copy.deepcopy(result)
    static = persisted.pop("static_analysis", None)
    row = RepoAnalysis(
        student_name=req.student_name.strip(),
        github_url=req.github_url.strip(),
        result_json=persisted,
        static_analysis_json=static,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    result["analysis_id"] = row.id
    try:
        validated = JudgeResult(**result)
        return validated.model_dump()
    except ValidationError as e:
        logger.error(f"Validation error in Repo Judge: {e}")
        return {
            "repo_url": req.github_url,
            "accessibility": "public",
            "languages": [],
            "scores": {
                "functionality": {"score": 0, "reasons": ["Validation failed"]},
                "code_quality": {"score": 0, "reasons": []},
                "documentation": {"score": 0, "reasons": []},
                "architecture": {"score": 0, "reasons": []},
                "testing_ci": {"score": 0, "reasons": []},
                "innovation_ux": {"score": 0, "reasons": []}
            },
            "total_score": 0,
            "strengths": [],
            "top_issues": [
                {
                    "severity": "critical",
                    "title": "Response Validation Failed",
                    "description": f"The AI response could not be mapped to the expected format: {e}",
                    "estimated_effort_hours": 0
                }
            ],
            "reproducibility": {"can_run": False},
            "mentor_notes": f"Error processing AI results: {e}",
            "student_name": req.student_name
        }
    except Exception as e:
        logger.exception("Unexpected error finalizing result")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error finalizing result: {e}",
        )