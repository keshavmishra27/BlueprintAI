import os
import logging
from typing import List, Optional

import requests as http_requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, ValidationError, model_validator
from typing import List, Optional

router = APIRouter(prefix="/repo-judge", tags=["Repo Judge"])
logger = logging.getLogger(__name__)

class AnalyzeRequest(BaseModel):

    github_url: str
    student_name: str = "Anonymous"


class ScoreDetail(BaseModel):
    score: float = 0.0
    weight: Optional[float] = 0.0
    reasons: List[str] = []

class Scores(BaseModel):
    functionality: ScoreDetail = ScoreDetail()
    code_quality: ScoreDetail = ScoreDetail()
    documentation: ScoreDetail = ScoreDetail()
    architecture: ScoreDetail = ScoreDetail()
    testing_ci: ScoreDetail = ScoreDetail()
    innovation_ux: ScoreDetail = ScoreDetail()

class IssueFile(BaseModel):
    path: str
    lines: str
    excerpt: Optional[str] = None

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
            # Map 'title' to 'type' if type is missing
            if 'title' in data and not data.get('type'):
                data['type'] = data['title']
            # Map 'lines' or 'description' to 'evidence' if evidence is missing
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
    # Keep compatibility with frontend if needed, or update frontend
    student_name: Optional[str] = None


def _check_ollama():
    """Verify Ollama is running, but skip if Gemini is configured."""
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key and google_key != "your_gemini_api_key_here":
        return  # Hybrid approach will use Gemini

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model    = os.getenv("OLLAMA_MODEL",    "llama3.2")
    try:
        r = http_requests.get(f"{base_url}/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        if not any(m.startswith(model.split(":")[0]) for m in models):
            raise HTTPException(
                status_code=503,
                detail=f"Model '{model}' not found in Ollama. Run: ollama pull {model}",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama is not running. Start it with: ollama serve  ({e})",
        )



@router.get(
    "/health",
    summary="Repo Judge health check",
)
def health():
    """Returns ok if the Repo Judge router is live."""
    return {"status": "ok", "route": "/repo-judge"}


@router.post(
    "/analyze",
    summary="Analyze a GitHub repo as a international hackathon judge",
    description=("""
You are an experienced international hackathon judge and technical mentor. Input: a PUBLIC GitHub repository URL. Your job: scrape the repository (all files, commit history optional), analyze it end-to-end, and deliver an expert, reproducible, and actionable judging report suitable for student grading and mentor feedback.

1) Mandatory checks (fail/notice conditions)
- Confirm repository is public and accessible; return an error if not.
- Confirm presence of a license file; flag missing or incompatible license.
- Confirm top-level README.md exists; if missing, treat as a documentation issue.
- Detect presence of obvious secrets (api keys, tokens) in repo; do not print secrets, but flag location and give remediation steps.

2) Analysis tasks (perform in order)
A. Project quick-run & reproducibility:
   - Identify language(s), runtime, and build system (e.g., Python/Node/Java/C++).
   - Find and list exact run/build commands (README, package.json, Makefile, Dockerfile, workflow files).
   - Attempt to run tests and/or start the app only if the environment is available. If you cannot run, say so and list the missing steps or secrets.
B. Functionality & correctness:
   - Inspect main features claimed in README and demo; check code paths that implement those features.
   - Verify presence and behavior of core modules; note unimplemented or stubbed features.
C. Code quality & maintainability:
   - Evaluate project structure, naming, modularity, duplication, complexity hotspots.
   - Identify specific functions/files that need refactor (include file paths and line ranges).
D. Architecture & design:
   - Evaluate separation of concerns, layering (UI/backend/db), and use of patterns.
   - Comment on scalability, coupling, and single-point-of-failure issues with examples.
E. Tests & CI:
   - Detect test suites, test coverage indicators, and CI workflows (GitHub Actions, Travis, etc.).
   - If tests exist, report test count and failures (if run). If no tests, recommend what to test and provide 3 example unit tests (test name + one-line description).
F. Documentation & onboarding:
   - Evaluate README completeness (setup, dev run, testing, architecture diagram, contribution guide).
   - Check for API docs, in-code comments, and inline docstrings.
G. Security, dependencies, and license:
   - List dependencies (requirements.txt, package.json) with their versions.
   - Flag outdated or known vulnerable dependencies (if you cannot query CVE DB, still call out unpinned ranges or wildly old versions).
   - Note license presence/type and compatibility issues.
H. UX & polish:
   - Comment on CLI/GUI friendliness, helpful error messages, and demo quality.

3) Output requirements (strict)
Produce two artifacts: (A) A structured JSON verdict and (B) a short human summary (3–6 sentences).

A. **Structured JSON format** (required keys)
{
  "repo_url": "<url>",
  "accessibility": "public" | "not_accessible",
  "languages": ["python","html",...],
  "scores": {
    "functionality": {"score": 0-10, "weight": 0.30, "reasons": ["...","..."]},
    "code_quality": {"score": 0-10, "weight": 0.20, "reasons": [...]},
    "documentation": {"score": 0-10, "weight": 0.15, "reasons": [...]},
    "architecture": {"score": 0-10, "weight": 0.15, "reasons": [...]},
    "testing_ci": {"score": 0-10, "weight": 0.10, "reasons": [...]},
    "innovation_ux": {"score": 0-10, "weight": 0.10, "reasons": [...]}
  },
  "total_score": 0-100,
  "strengths": ["short bullets - include file paths where relevant"],
  "top_issues": [
    {
      "severity": "critical"|"major"|"minor"|"suggestion",
      "title": "Short issue title",
      "description": "Why and how to fix",
      "files": [{"path":"src/foo.py","lines":"23-45","excerpt":"... up to 3 lines ..."}],
      "estimated_effort_hours": 1.5
    },
    ...
  ],
  "suggested_github_issues": [
    {"title":"Fix X", "body":"Detailed steps + commands + tests to add", "labels":["bug","help-wanted"]},
    ...
  ],
  "security_warnings": [
    {"type":"secret_leak"|"vuln_dependency"|"unsafe_eval", "evidence":"file path and short excerpt", "remediation":"..."}
  ],
  "reproducibility": {
    "can_run": true|false,
    "run_commands":["..."],
    "notes": "env vars required, DB steps, etc."
  },
  "recommended_tests": [
    {"name":"test_core_login", "description":"Unit test for login success/failure", "file":"tests/test_auth.py"}
  ],
  "mentor_notes": "A short mentoring paragraph (50-120 words) with tone: constructive and direct."
}

B. **Human summary** (plain text) — 3–6 sentences highlighting overall verdict and 2 top priorities.

4) Scoring guidance (how to map 0–10)
- 9–10: Excellent, production-grade for its scope; clean code; tests; docs; no critical bugs.
- 7–8: Very good; minor polish or missing tests/docs.
- 4–6: Functional but needs notable improvements (tests, structure, docs).
- 1–3: Incomplete or brittle; critical issues present.
- 0: Non-functional or mostly placeholder.

5) Evidence & quoting rules
- Always attach at least one file path for every major claim.
- Only include short code excerpts (≤3 lines) and annotate line numbers.
- If you run commands, show exact commands and their raw outputs; otherwise label analysis as "static-only".

6) Deliver human-readable remediation guidance
- For each top_issue include step-by-step fix plan and an estimated effort (hours).
- Offer 3 example GitHub issue templates with title/body/labels for a mentor to assign to the student.

7) Tone & constraints
- Be factual, constructive, and kind. Avoid shaming language.
- Do not fabricate running results or dates. If you can't verify something, say "not verified" and why.

If the repository is inaccessible or private, return a JSON with accessibility:"not_accessible" and a short reason. End.

"""  ),
)
def analyze_repo(req: AnalyzeRequest):
    """
    1. Validates the GitHub URL.
    2. Scrapes all readable code files via the GitHub Contents API.
    3. Sends the code to the local Ollama LLM.
    4. Returns a structured judge result.
    """
    if not req.github_url.strip():
        raise HTTPException(status_code=400, detail="github_url cannot be empty.")
    if not req.student_name.strip():
        raise HTTPException(status_code=400, detail="student_name cannot be empty.")

    _check_ollama()

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

    
    # Ensure nested objects are handled correctly if needed
    # (Pydantic will handle dict to model conversion automatically in response_model)
    pass

    try:
        # Validate but return a dict for better serialization safety
        validated = JudgeResult(**result)
        return validated.dict()
    except ValidationError as e:
        logger.error(f"Validation error in Repo Judge: {e}")
        # Return a safe, valid-schema fallback if Pydantic fails
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
