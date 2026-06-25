"""
Option A – GitHub Webhook receiver.
POST /webhooks/github  →  receives push events, enqueues automatic repo analysis.
POST /webhooks/register →  register a repo for webhook-driven auto-analysis.
GET  /webhooks/repos    →  list registered repos.
"""
import hashlib
import hmac
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models import WebhookRepo
from backend.app.services.task_queue import enqueue
router = APIRouter(prefix="/webhooks", tags=["GitHub Webhooks"])
logger = logging.getLogger(__name__)
class RegisterRequest(BaseModel):
    github_url: str
    student_name: str = "Anonymous"
    secret: str | None = None
class RegisteredRepo(BaseModel):
    id: int
    github_url: str
    student_name: str
    active: bool
    last_push_sha: str | None = None
    last_task_id: str | None = None
    registered_at: str | None = None
def _verify_signature(body: bytes, secret: str, header_sig: str | None) -> bool:
    """Validate X-Hub-Signature-256 from GitHub."""
    if not header_sig:
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header_sig)
def _normalize_url(url: str) -> str:
    """Normalize a GitHub URL to https://github.com/owner/repo."""
    url = url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    return url
def _extract_repo_url_from_payload(payload: dict) -> str | None:
    """Pull the HTML URL from a GitHub webhook payload."""
    repo = payload.get("repository")
    if repo and repo.get("html_url"):
        return _normalize_url(repo["html_url"])
    return None
def _handle_webhook_repo_judge(payload: dict) -> dict:
    """Run the full repo judge pipeline (download → static → CrewAI)."""
    from backend.app.services.github_judge_service import analyze_repo
    return analyze_repo(
        github_url=payload["github_url"],
        student_name=payload["student_name"],
    )
@router.get("/health")
def health():
    return {"status": "ok", "route": "/webhooks"}
@router.post("/register")
def register_repo(req: RegisterRequest):
    """Register a GitHub repo so pushes automatically trigger CrewAI analysis."""
    url = _normalize_url(req.github_url)
    if not url.startswith("https://github.com/"):
        raise HTTPException(status_code=400, detail="URL must be a github.com repo.")
    db = SessionLocal()
    try:
        existing = db.query(WebhookRepo).filter(WebhookRepo.github_url == url).first()
        if existing:
            existing.active = True
            existing.student_name = req.student_name
            existing.secret = req.secret
            db.commit()
            return {"message": "Repo already registered — reactivated.", "id": existing.id}
        row = WebhookRepo(
            github_url=url,
            student_name=req.student_name,
            secret=req.secret,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {
            "message": "Repo registered for webhook automation.",
            "id": row.id,
            "webhook_url": "/webhooks/github",
            "instructions": (
                f"In your GitHub repo → Settings → Webhooks → Add webhook. "
                f"Set Payload URL to <your-server>/webhooks/github, "
                f"Content type: application/json, "
                f"Secret: {req.secret or '(none)'}, "
                f"Events: Just the push event."
            ),
        }
    finally:
        db.close()
@router.get("/repos", response_model=List[RegisteredRepo])
def list_repos():
    """List all registered webhook repos."""
    db = SessionLocal()
    try:
        rows = db.query(WebhookRepo).order_by(WebhookRepo.registered_at.desc()).all()
        return [
            RegisteredRepo(
                id=r.id,
                github_url=r.github_url,
                student_name=r.student_name,
                active=r.active,
                last_push_sha=r.last_push_sha,
                last_task_id=r.last_task_id,
                registered_at=r.registered_at.isoformat() if r.registered_at else None,
            )
            for r in rows
        ]
    finally:
        db.close()
@router.post("/github")
async def github_webhook(request: Request):
    """
    Receive GitHub push webhook events.
    When a push is received for a registered repo, a background CrewAI
    analysis task is automatically enqueued — zero-touch code evaluation.
    """
    body = await request.body()
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")
    event = request.headers.get("X-GitHub-Event", "ping")
    if event == "ping":
        return {"msg": "pong 🏓"}
    if event != "push":
        return {"msg": f"Ignored event: {event}"}
    repo_url = _extract_repo_url_from_payload(payload)
    if not repo_url:
        raise HTTPException(status_code=400, detail="Could not extract repo URL.")
    db = SessionLocal()
    try:
        reg = db.query(WebhookRepo).filter(
            WebhookRepo.github_url == repo_url,
            WebhookRepo.active == True,
        ).first()
        if not reg:
            return {"msg": f"Repo {repo_url} not registered — ignoring."}
        if reg.secret:
            sig = request.headers.get("X-Hub-Signature-256")
            if not _verify_signature(body, reg.secret, sig):
                raise HTTPException(status_code=403, detail="Invalid webhook signature.")
        head_sha = payload.get("after", "")[:12]
        logger.info(
            "Webhook push received: %s (sha=%s) – enqueuing auto-analysis",
            repo_url, head_sha,
        )
        task_id = enqueue("webhook_repo_judge", {
            "github_url": reg.github_url,
            "student_name": reg.student_name,
        })
        reg.last_push_sha = head_sha
        reg.last_task_id = task_id
        db.commit()
        return {
            "msg": "Auto-analysis enqueued.",
            "task_id": task_id,
            "repo": repo_url,
            "sha": head_sha,
        }
    finally:
        db.close()
