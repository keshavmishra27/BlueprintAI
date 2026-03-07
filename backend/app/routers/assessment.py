"""
assessment.py  (router)
-----------------------
FastAPI router for the MCQ-based assessment.
Prefix: /assess   Tag: Assessment

Endpoints
---------
GET  /assess/domains       — list available domains
POST /assess/generate-mcq  — generate 15 MCQs for a domain
POST /assess/submit-mcq    — grade user answers and return percentile
GET  /assess/results        — list all past sessions
GET  /assess/results/{id}   — get one session result
DELETE /assess/sessions/{id}
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests as http_requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import AssessmentSession

router = APIRouter(prefix="/assess", tags=["Assessment"])

AVAILABLE_DOMAINS = [
    "Web Development",
    "Machine Learning",
    "Cybersecurity",
    "Cloud Computing",
    "App Development",
    "Agentic AI",
]


# ── Request / Response schemas ──────────────────────────────────────

class GenerateMCQRequest(BaseModel):
    student_name: str
    domain: str


class QuestionOut(BaseModel):
    """Question sent to the frontend — NO correct_answer."""
    index: int
    question: str
    options: List[str]
    difficulty: str


class GenerateMCQResponse(BaseModel):
    session_id: int
    student_name: str
    domain: str
    questions: List[QuestionOut]


class SubmitMCQRequest(BaseModel):
    session_id: int
    answers: Dict[str, str]   # {"0": "A", "1": "C", ...}


class SubmitMCQResponse(BaseModel):
    session_id: int
    student_name: str
    domain: str
    scores: dict


class SessionSummary(BaseModel):
    id: int
    student_name: str
    domains: List[str]
    status: str
    total_score: Optional[int]
    created_at: str


# ── Helpers ─────────────────────────────────────────────────────────

def _check_ollama():
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


def _get_session(session_id: int, db: Session) -> AssessmentSession:
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    return session


# ── Endpoints ───────────────────────────────────────────────────────

@router.get(
    "/domains",
    response_model=List[str],
    summary="List available assessment domains",
)
def list_domains():
    return AVAILABLE_DOMAINS


@router.post(
    "/generate-mcq",
    response_model=GenerateMCQResponse,
    summary="Generate 15 MCQ questions for a domain",
    description=(
        "Provide student name and a domain. The AI generates 15 MCQs "
        "(5 easy, 5 medium, 5 hard). Questions are returned WITHOUT "
        "correct answers — those are stored server-side for grading."
    ),
)
def generate_mcq(req: GenerateMCQRequest, db: Session = Depends(get_db)):
    if not req.student_name.strip():
        raise HTTPException(status_code=400, detail="student_name cannot be empty.")
    if not req.domain.strip():
        raise HTTPException(status_code=400, detail="domain cannot be empty.")

    _check_ollama()

    from backend.app.services.mcq_service import generate_mcq as run_generate

    try:
        questions = run_generate(domain=req.domain.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCQ generation failed: {e}")

    # Save to DB — transcript stores the full questions (with answers)
    session = AssessmentSession(
        student_name=req.student_name.strip(),
        domains=[req.domain.strip()],
        transcript=questions,          # full questions with correct_answer
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Return questions WITHOUT correct_answer
    questions_out = [
        QuestionOut(
            index=i,
            question=q.get("question", ""),
            options=q.get("options", []),
            difficulty=q.get("difficulty", "medium"),
        )
        for i, q in enumerate(questions)
    ]

    return GenerateMCQResponse(
        session_id=session.id,
        student_name=session.student_name,
        domain=req.domain.strip(),
        questions=questions_out,
    )


@router.post(
    "/submit-mcq",
    response_model=SubmitMCQResponse,
    summary="Submit MCQ answers and get score + percentile",
)
def submit_mcq(req: SubmitMCQRequest, db: Session = Depends(get_db)):
    session = _get_session(req.session_id, db)

    if session.status == "scored":
        return SubmitMCQResponse(
            session_id=session.id,
            student_name=session.student_name,
            domain=session.domains[0] if session.domains else "",
            scores=session.scores,
        )

    from backend.app.services.mcq_service import grade_answers

    scores = grade_answers(
        questions=session.transcript,
        answers=req.answers,
    )

    session.scores = scores
    session.status = "scored"
    session.completed_at = datetime.now(timezone.utc)
    db.commit()

    return SubmitMCQResponse(
        session_id=session.id,
        student_name=session.student_name,
        domain=session.domains[0] if session.domains else "",
        scores=scores,
    )


@router.get(
    "/results",
    response_model=List[SessionSummary],
    summary="List all assessment results",
)
def list_results(db: Session = Depends(get_db)):
    sessions = (
        db.query(AssessmentSession)
        .order_by(AssessmentSession.created_at.desc())
        .all()
    )
    return [
        SessionSummary(
            id=s.id,
            student_name=s.student_name,
            domains=s.domains,
            status=s.status,
            total_score=s.scores.get("correct") if s.scores else None,
            created_at=s.created_at.isoformat() if s.created_at else "",
        )
        for s in sessions
    ]


@router.get(
    "/results/{session_id}",
    response_model=SubmitMCQResponse,
    summary="Get result for one session",
)
def get_result(session_id: int, db: Session = Depends(get_db)):
    session = _get_session(session_id, db)
    if session.status != "scored":
        raise HTTPException(status_code=400, detail="This session has not been scored yet.")
    return SubmitMCQResponse(
        session_id=session.id,
        student_name=session.student_name,
        domain=session.domains[0] if session.domains else "",
        scores=session.scores,
    )


@router.delete(
    "/sessions/{session_id}",
    summary="Delete an assessment session",
)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = _get_session(session_id, db)
    db.delete(session)
    db.commit()
    return {"message": f"Session {session_id} deleted."}
