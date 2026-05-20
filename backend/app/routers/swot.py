from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.rate_limit import limiter
from backend.app.models import SwotAnalysis
from backend.app.services.llm_factory import check_llm_availability

router = APIRouter(prefix="/swot", tags=["SWOT Analysis"])


class SwotRequest(BaseModel):
    subject_name: str
    subject_type: str  # "project" | "idea"
    description: str


class SwotResultSummary(BaseModel):
    id: int
    subject_name: str
    subject_type: str
    created_at: str


@router.get("/health")
def health():
    return {"status": "ok", "route": "/swot"}


@router.post("/analyze")
@limiter.limit("5/minute")
def analyze_swot(request: Request, req: SwotRequest, db: Session = Depends(get_db)):
    if not req.subject_name.strip():
        raise HTTPException(status_code=400, detail="subject_name cannot be empty.")
    if req.subject_type not in ("project", "idea"):
        raise HTTPException(status_code=400, detail="subject_type must be 'project' or 'idea'.")
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="description cannot be empty.")

    check_llm_availability()
    from backend.app.services.swot_service import analyze_swot as run_swot

    try:
        result = run_swot(req.subject_name.strip(), req.subject_type, req.description.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SWOT analysis failed: {e}")

    row = SwotAnalysis(
        subject_name=req.subject_name.strip(),
        subject_type=req.subject_type,
        description=req.description.strip(),
        result_json=result,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    result["id"] = row.id
    return result


@router.get("/results", response_model=List[SwotResultSummary])
def list_swot_results(db: Session = Depends(get_db)):
    rows = db.query(SwotAnalysis).order_by(SwotAnalysis.created_at.desc()).limit(50).all()
    return [
        SwotResultSummary(
            id=r.id,
            subject_name=r.subject_name,
            subject_type=r.subject_type,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in rows
    ]


@router.get("/results/{result_id}")
def get_swot_result(result_id: int, db: Session = Depends(get_db)):
    row = db.query(SwotAnalysis).filter(SwotAnalysis.id == result_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="SWOT result not found.")
    return row.result_json
