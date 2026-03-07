"""
project_suggest.py
------------------
FastAPI router for the Project Suggestion feature.
Prefix: /project-suggest   Tag: Project Suggest

Endpoints
---------
POST /project-suggest/suggest  — get AI-generated project ideas for a theme
GET  /project-suggest/health   — simple liveness probe
"""

import os
from typing import List

import requests as http_requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/project-suggest", tags=["Project Suggest"])


# ── Request / Response schemas ──────────────────────────────────────

class SuggestRequest(BaseModel):
    theme: str


class ProjectItem(BaseModel):
    title: str = ""
    description: str = ""
    tech_stack: List[str] = []
    why_great_for_resume: str = ""
    why_it_wins: str = ""


class SuggestResult(BaseModel):
    theme: str
    resume_projects: List[ProjectItem] = []
    hackathon_projects: List[ProjectItem] = []


# ── Helpers ─────────────────────────────────────────────────────────

def _check_ollama():
    """Verify Ollama is running before hitting it."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
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


# ── Endpoints ───────────────────────────────────────────────────────

@router.get("/health", summary="Project Suggest health check")
def health():
    """Returns ok if the Project Suggest router is live."""
    return {"status": "ok", "route": "/project-suggest"}


@router.post(
    "/suggest",
    response_model=SuggestResult,
    summary="Get AI-powered project suggestions for a theme",
    description=(
        "Provide a theme or domain (e.g. 'AI', 'FinTech', 'Healthcare'). "
        "The agent will return 5 industry-grade resume project ideas and "
        "5 hackathon-winning project ideas with detailed descriptions."
    ),
)
def suggest_projects(req: SuggestRequest):
    theme = req.theme.strip()
    if not theme:
        raise HTTPException(status_code=400, detail="theme cannot be empty.")

    _check_ollama()

    from backend.app.services.project_suggest_service import suggest_projects as run_suggest

    try:
        data = run_suggest(theme=theme)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Suggestion failed: {e}",
        )

    # Normalise into ProjectItem-compatible dicts
    resume = []
    for p in data.get("resume_projects", []):
        if isinstance(p, dict):
            resume.append(ProjectItem(**{k: p.get(k, "") for k in ProjectItem.model_fields}))
    hackathon = []
    for p in data.get("hackathon_projects", []):
        if isinstance(p, dict):
            hackathon.append(ProjectItem(**{k: p.get(k, "") for k in ProjectItem.model_fields}))

    return SuggestResult(
        theme=theme,
        resume_projects=resume,
        hackathon_projects=hackathon,
    )
