"""
Option B – Task status polling endpoint.
GET /tasks/{task_id}  →  current status + result when done.
GET /tasks             →  recent tasks (newest first).
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from backend.app.database import SessionLocal
from backend.app.models import BackgroundTask
from backend.app.services.task_queue import get_task
router = APIRouter(prefix="/tasks", tags=["Background Tasks"])
class TaskStatus(BaseModel):
    id: str
    task_type: str
    status: str
    payload: dict | None = None
    result: dict | None = None
    error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
@router.get("/health")
def health():
    return {"status": "ok", "route": "/tasks"}
@router.get("/{task_id}", response_model=TaskStatus)
def poll_task(task_id: str):
    """Poll the current status of a background task."""
    info = get_task(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="Task not found.")
    return info
@router.get("", response_model=List[TaskStatus])
def list_recent_tasks(limit: int = Query(20, ge=1, le=100)):
    """List the most recent background tasks (newest first)."""
    db = SessionLocal()
    try:
        rows = (
            db.query(BackgroundTask)
            .order_by(BackgroundTask.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            TaskStatus(
                id=r.id,
                task_type=r.task_type,
                status=r.status,
                payload=r.payload_json,
                result=r.result_json,
                error=r.error,
                created_at=r.created_at.isoformat() if r.created_at else None,
                updated_at=r.updated_at.isoformat() if r.updated_at else None,
            )
            for r in rows
        ]
    finally:
        db.close()
