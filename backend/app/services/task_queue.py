"""
Option B – In-process async task queue backed by threads + DB.
Usage:
    task_id = enqueue("repo_judge", {"github_url": "...", "student_name": "..."})
    # ... later ...
    status = get_task(task_id)   # {"id": ..., "status": "done", "result_json": {...}}
"""
import logging
import threading
import uuid
from datetime import datetime, timezone
from backend.app.database import SessionLocal
from backend.app.models import BackgroundTask
logger = logging.getLogger(__name__)
_HANDLERS: dict[str, callable] = {}
def register_handler(task_type: str, fn: callable):
    """Register a function to be called for a given task_type."""
    _HANDLERS[task_type] = fn
    logger.info("Registered async handler for task_type=%s", task_type)
def enqueue(task_type: str, payload: dict) -> str:
    """Create a BackgroundTask row and spawn a daemon thread to execute it."""
    task_id = uuid.uuid4().hex
    db = SessionLocal()
    try:
        row = BackgroundTask(
            id=task_id,
            task_type=task_type,
            status="pending",
            payload_json=payload,
        )
        db.add(row)
        db.commit()
    finally:
        db.close()
    thread = threading.Thread(
        target=_run_task, args=(task_id, task_type, payload), daemon=True
    )
    thread.start()
    logger.info("Enqueued task %s (type=%s)", task_id, task_type)
    return task_id
def get_task(task_id: str) -> dict | None:
    """Return the current state of a background task."""
    db = SessionLocal()
    try:
        row = db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
        if not row:
            return None
        return {
            "id": row.id,
            "task_type": row.task_type,
            "status": row.status,
            "payload": row.payload_json,
            "result": row.result_json,
            "error": row.error,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
    finally:
        db.close()
def _run_task(task_id: str, task_type: str, payload: dict):
    """Execute the registered handler and persist the result."""
    db = SessionLocal()
    try:
        row = db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
        if not row:
            return
        row.status = "running"
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        handler = _HANDLERS.get(task_type)
        if not handler:
            row.status = "failed"
            row.error = f"No handler registered for task_type={task_type}"
            row.updated_at = datetime.now(timezone.utc)
            db.commit()
            return
        try:
            result = handler(payload)
            row.status = "done"
            row.result_json = result
        except Exception as exc:
            logger.exception("Task %s failed", task_id)
            row.status = "failed"
            row.error = str(exc)
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        logger.exception("Fatal error in task runner for %s", task_id)
    finally:
        db.close()
