"""
Automation dashboard endpoints.
Combines visibility into all three automation features:
- Option A (webhooks): see /webhooks/*
- Option B (background tasks): see /tasks/*
- Option C (scheduler + skill-gap reports): see below.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from backend.app.database import SessionLocal
from backend.app.models import SkillGapReport
from backend.app.services.scheduler import get_scheduler_status, run_skill_gap_job
from backend.app.services.task_queue import enqueue
router = APIRouter(prefix="/automation", tags=["Automation"])
class SchedulerInfo(BaseModel):
    running: bool
    jobs: list
class SkillGapSummary(BaseModel):
    id: int
    students_analyzed: int | None = None
    generated_at: str | None = None
@router.get("/health")
def health():
    return {"status": "ok", "route": "/automation"}
@router.get("/scheduler", response_model=SchedulerInfo)
def scheduler_status():
    """Show scheduler status and next run times."""
    return get_scheduler_status()
@router.post("/scheduler/run-now")
def trigger_skill_gap_now():
    """
    Manually trigger the nightly skill-gap analysis right now
    (runs in background thread via task queue).
    """
    task_id = enqueue("skill_gap_analysis", {})
    return {
        "message": "Skill-gap analysis enqueued.",
        "task_id": task_id,
    }
@router.get("/skill-gap-reports", response_model=List[SkillGapSummary])
def list_reports(limit: int = Query(10, ge=1, le=50)):
    """List recent skill-gap reports (newest first)."""
    db = SessionLocal()
    try:
        rows = (
            db.query(SkillGapReport)
            .order_by(SkillGapReport.generated_at.desc())
            .limit(limit)
            .all()
        )
        return [
            SkillGapSummary(
                id=r.id,
                students_analyzed=(r.report_json or {}).get("students_analyzed"),
                generated_at=r.generated_at.isoformat() if r.generated_at else None,
            )
            for r in rows
        ]
    finally:
        db.close()
@router.get("/skill-gap-reports/{report_id}")
def get_report(report_id: int):
    """Get the full JSON of a specific skill-gap report."""
    db = SessionLocal()
    try:
        row = db.query(SkillGapReport).filter(SkillGapReport.id == report_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Report not found.")
        return row.report_json
    finally:
        db.close()
