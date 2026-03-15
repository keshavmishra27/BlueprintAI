"""
repo_judge.py
-------------
FastAPI router for the GitHub Repo Judge feature.
Prefix: /repo-judge   Tag: Repo Judge

Endpoints
---------
POST /repo-judge/analyze  — scrape a public GitHub repo and get hackathon judge feedback
GET  /repo-judge/health   — simple liveness probe
"""

import os
import logging
from typing import List, Optional

import requests as http_requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, ValidationError

router = APIRouter(prefix="/repo-judge", tags=["Repo Judge"])
logger = logging.getLogger(__name__)

class AnalyzeRequest(BaseModel):

    github_url: str
    student_name: str = "Anonymous"


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
    response_model=JudgeResult,
    summary="Analyze a GitHub repo as a international hackathon judge",
    description=(
        "Provide the URL of any **public** GitHub repository. "
        "The agent will scrape the code, read it in full, and return "
        "a structured international hackathon judge verdict with scores, strengths, "
        "and specific improvements your student should make."
    ),
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

    from backend.app.services.github_judge_service import analyze_repo as run_analysis

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

    
    for score_field in (
        "overall_score", "code_quality_score",
        "innovation_score", "completeness_score", "documentation_score",
    ):
        try:
            result[score_field] = int(result.get(score_field, 0))
        except (TypeError, ValueError):
            result[score_field] = 0

# Ensure list fields are actually lists
    for list_field in ("strengths", "improvements", "standout_files", "problem_areas"):
        if not isinstance(result.get(list_field), list):
            result[list_field] = []

    try:
        return JudgeResult(**result)
    except ValidationError as e:
        logger.error(f"Validation error in Repo Judge: {e}")
        # Return a safe, valid-schema fallback if Pydantic fails
        return JudgeResult(
            student_name=req.student_name,
            repository=req.github_url,
            overall_score=0,
            verdict="Validation failed for AI response.",
            hackathon_readiness=f"Error: {e}",
            improvements=[
                Improvement(
                    file="System",
                    issue="Response validation failed.",
                    fix="Check the logs for technical details."
                )
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error finalizing result: {e}",
        )
