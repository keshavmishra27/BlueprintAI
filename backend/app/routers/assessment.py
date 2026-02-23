import os
from datetime import datetime, timezone
from typing import List, Optional
import requests as http_requests

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import AssessmentSession

router = APIRouter(prefix="/assess", tags=["Assessment"])

# Available domains students can pick from
AVAILABLE_DOMAINS = [
    "Web Development",
    "Machine Learning",
    "Cybersecurity",
    "Cloud Computing",
    "App Development",
    "Agentic AI"
]


# Schemas
class StartSessionRequest(BaseModel):
    student_name: str
    domains: List[str]


class StartSessionResponse(BaseModel):
    session_id: int
    student_name: str
    domains: List[str]
    message: str 


class ChatRequest(BaseModel):
    session_id: int
    student_message: str


class ChatResponse(BaseModel):
    agent_reply: str
    turn_count: int


class ScoreResponse(BaseModel):
    session_id: int
    student_name: str
    domains: List[str]
    scores: dict
    turn_count: int


class SessionSummary(BaseModel):
    id: int
    student_name: str
    domains: List[str]
    status: str
    total_score: Optional[int]
    created_at: str


# Helpers

def _check_ollama():
    """Verify Ollama is running and the configured model is available."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model    = os.getenv("OLLAMA_MODEL", "llama3.2")
    try:
        r = http_requests.get(f"{base_url}/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        if not any(m.startswith(model.split(":")[0]) for m in models):
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Model '{model}' not found in Ollama. "
                    f"Run: ollama pull {model}"
                ),
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


# Routes

@router.get(
    "/domains",
    response_model=List[str],
    summary="List available assessment domains",
)
def list_domains():
    """Returns all domains a student can choose for their assessment."""
    return AVAILABLE_DOMAINS


@router.post(
    "/start",
    response_model=StartSessionResponse,
    summary="Start a new assessment session",
    description="Create a new session for a student. Returns the agent's opening message.",
)
def start_session(req: StartSessionRequest, db: Session = Depends(get_db)):
    _check_ollama()

    if not req.student_name.strip():
        raise HTTPException(status_code=400, detail="student_name cannot be empty.")
    if not req.domains:
        raise HTTPException(status_code=400, detail="Select at least one domain.")

    from backend.app.services.crew_service import get_interviewer_response

    opening = get_interviewer_response(
        student_name=req.student_name.strip(),
        domains=req.domains,
        conversation_history=[],
        student_message="Hello, I'm ready to start.",
    )

    initial_transcript = [
        {"role": "student", "content": "Hello, I'm ready to start."},
        {"role": "agent",   "content": opening},
    ]

    session = AssessmentSession(
        student_name=req.student_name.strip(),
        domains=req.domains,
        transcript=initial_transcript,
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return StartSessionResponse(
        session_id=session.id,
        student_name=session.student_name,
        domains=session.domains,
        message=opening,
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message and get the agent's reply",
)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    _check_ollama()
    session = _get_session(req.session_id, db)

    if session.status == "scored":
        raise HTTPException(status_code=400, detail="This session has already been scored.")

    if not req.student_message.strip():
        raise HTTPException(status_code=400, detail="student_message cannot be empty.")

    from backend.app.services.crew_service import get_interviewer_response

    reply = get_interviewer_response(
        student_name=session.student_name,
        domains=session.domains,
        conversation_history=session.transcript,
        student_message=req.student_message.strip(),
    )

    # Append to transcript``
    updated = list(session.transcript)
    updated.append({"role": "student", "content": req.student_message.strip()})
    updated.append({"role": "agent",   "content": reply})
    session.transcript = updated
    db.commit()

    return ChatResponse(
        agent_reply=reply,
        turn_count=len([t for t in updated if t["role"] == "student"]),
    )


@router.post(
    "/score/{session_id}",
    response_model=ScoreResponse,
    summary="End session and generate productivity score",
    description=(
        "Triggers the CrewAI scorer to analyze the full transcript "
        "and return a structured productivity score with feedback."
    ),
)
def score_session(session_id: int, db: Session = Depends(get_db)):
    _check_ollama()
    session = _get_session(session_id, db)

    if session.status == "scored":
        return ScoreResponse(
            session_id=session.id,
            student_name=session.student_name,
            domains=session.domains,
            scores=session.scores,
            turn_count=len([t for t in session.transcript if t["role"] == "student"]),
        )

    student_turns = [t for t in session.transcript if t["role"] == "student"]
    if len(student_turns) < 2:
        raise HTTPException(
            status_code=400,
            detail="Not enough conversation to score. Have at least 2 exchanges with the agent.",
        )

    from backend.app.services.crew_service import score_session as run_scorer

    scores = run_scorer(
        student_name=session.student_name,
        domains=session.domains,
        conversation_history=session.transcript,
    )

    session.scores = scores
    session.status = "scored"
    session.completed_at = datetime.now(timezone.utc)
    db.commit()

    return ScoreResponse(
        session_id=session.id,
        student_name=session.student_name,
        domains=session.domains,
        scores=scores,
        turn_count=len(student_turns),
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
            total_score=s.scores.get("total") if s.scores else None,
            created_at=s.created_at.isoformat() if s.created_at else "",
        )
        for s in sessions
    ]


@router.get(
    "/results/{session_id}",
    response_model=ScoreResponse,
    summary="Get full result for one session",
)
def get_result(session_id: int, db: Session = Depends(get_db)):
    session = _get_session(session_id, db)
    if session.status != "scored":
        raise HTTPException(status_code=400, detail="This session has not been scored yet.")
    return ScoreResponse(
        session_id=session.id,
        student_name=session.student_name,
        domains=session.domains,
        scores=session.scores,
        turn_count=len([t for t in session.transcript if t["role"] == "student"]),
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
