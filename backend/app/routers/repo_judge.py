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
    "functionality": {"score": 0, "weight": 0.25, "reasons": ["<your detailed analysis>"]},
    "code_quality":  {"score": 0, "weight": 0.20, "reasons": ["<your detailed analysis>"]},
    "documentation": {"score": 0, "weight": 0.15, "reasons": ["<your detailed analysis>"]},
    "architecture":  {"score": 0, "weight": 0.15, "reasons": ["<your detailed analysis>"]},
    "testing_ci":    {"score": 0, "weight": 0.10, "reasons": ["<your detailed analysis>"]},
    "innovation_ux": {"score": 0, "weight": 0.15, "reasons": ["<your detailed analysis>"]}
  },
  "total_score": 0,
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
  "coding_style_summary": "Paragraph about naming, modularity, consistency.",
  "hackathon_recommendations": [
    {
      "name": "Hackathon Name",
      "description": "Brief description of the hackathon",
      "date": "Month YYYY or Recurring",
      "registration_link": "https://example.com/register"
    }
  ]
}"""

SCORING_RUBRIC = """\
SCORING RUBRIC — assign each score 1-10 based on ACTUAL code analysis. Do NOT default to mid-range scores.

FUNCTIONALITY (weight 0.25):
  1-3: Barely works, crashes, missing core features
  4-5: Basic functionality present but incomplete or buggy
  6-7: Core features work well, some edge cases missed
  8-10: Fully functional, robust, handles edge cases

CODE QUALITY (weight 0.20):
  1-3: Messy spaghetti code, no patterns, poor naming
  4-5: Some structure but inconsistent style, code smells
  6-7: Clean code, follows conventions, reasonable patterns
  8-10: Professional-grade, DRY, SOLID principles, best practices

DOCUMENTATION (weight 0.15):
  1-3: No README or docs at all
  4-5: Minimal README, missing setup/usage instructions
  6-7: Good README with setup guide, some inline comments
  8-10: Comprehensive docs, API reference, architecture notes, examples

ARCHITECTURE (weight 0.15):
  1-3: Everything in one file, no separation of concerns
  4-5: Basic file splitting but flat structure
  6-7: Clear module boundaries, reasonable separation of concerns
  8-10: Multi-layer architecture (routers/services/models), design patterns, scalable

TESTING & CI (weight 0.10):
  1-3: No tests at all, no CI
  4-5: One or two tests or basic CI only
  6-7: Decent test coverage, CI pipeline exists
  8-10: Thorough tests, multiple test types, CI/CD pipeline

INNOVATION & UX (weight 0.15):
  1-3: Common tutorial clone (calculator, todo, tic-tac-toe), no originality
  4-5: Minor twist on a well-known concept
  6-7: Some novel aspects, solves a real need, decent UX
  8-10: Creative solution to real problem, polished experience, original approach

CALIBRATION — use these as anchors:
- Single-file game (tic-tac-toe, snake, quiz): architecture 2-3, innovation 2-3, testing 1-2
- Static website / portfolio: architecture 3-4, innovation 2-4
- Multi-page CRUD app (blog, todo): architecture 4-6, innovation 3-5
- Full-stack app with API + DB + frontend: architecture 6-8
- Full-stack with AI/ML agents, background jobs, webhooks: architecture 7-9, innovation 7-9

CRITICAL: Differentiate aggressively. A tic-tac-toe game CANNOT score the same as a full-stack AI platform.
"""

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
    name: Optional[str] = "Recommended Test"
    description: Optional[str] = "No description provided."
    file: Optional[str] = ""
    @model_validator(mode='before')
    @classmethod
    def coerce_string(cls, data):
        if isinstance(data, str):
            return {"name": "Recommended Test", "description": data, "file": data}
        return data

class HackathonRecommendation(BaseModel):
    name: str
    description: Optional[str] = ""
    date: Optional[str] = ""
    registration_link: Optional[str] = ""

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
    hackathon_recommendations: List[HackathonRecommendation] = []
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
            # ── Recalculate total_score from weighted dimension scores ──
            # Never trust the LLM to do arithmetic; compute server-side.
            scores_data = data.get('scores')
            if isinstance(scores_data, dict):
                _default_weights = {
                    'functionality': 0.25, 'code_quality': 0.20,
                    'documentation': 0.15, 'architecture': 0.15,
                    'testing_ci': 0.10, 'innovation_ux': 0.15,
                }
                w_sum = 0.0
                ws_sum = 0.0
                for dim, dw in _default_weights.items():
                    val = scores_data.get(dim)
                    if val is None:
                        continue
                    if isinstance(val, (int, float)):
                        s, w = float(val), dw
                    elif isinstance(val, dict):
                        s = float(val.get('score', 0))
                        w = float(val.get('weight', dw))
                    else:
                        continue
                    ws_sum += s * w
                    w_sum += w
                if w_sum > 0:
                    data['total_score'] = round((ws_sum / w_sum) * 10, 1)
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
            "student_name": req.student_name,
            "hackathon_recommendations": []
        }
    except Exception as e:
        logger.exception("Unexpected error finalizing result")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error finalizing result: {e}",
        )