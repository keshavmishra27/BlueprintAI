import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.config import get_settings
from backend.app.database import ensure_schema
from backend.app.middleware.auth import APIKeyMiddleware
from backend.app.middleware.rate_limit import limiter
from backend.app.routers import assessment, repo_judge, project_suggest, idea_validator
from backend.app.routers import tasks, webhooks, automation

logging.basicConfig(level=logging.INFO)

try:
    ensure_schema()
except Exception as e:
    logging.warning("Schema setup issue at startup: %s", e)


# ── Register background-task handlers (Option A + B + C) ─────────────────────

def _register_task_handlers():
    from backend.app.services.task_queue import register_handler
    from backend.app.routers.webhooks import _handle_webhook_repo_judge
    from backend.app.services.scheduler import run_skill_gap_job

    # Option A: webhook-triggered repo analysis
    register_handler("webhook_repo_judge", _handle_webhook_repo_judge)

    # Option C: scheduled skill-gap analysis (also triggered manually)
    register_handler("skill_gap_analysis", lambda _payload: run_skill_gap_job() or {})

_register_task_handlers()


# ── App lifecycle (scheduler start/stop) ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.app.services.scheduler import start_scheduler, stop_scheduler
    start_scheduler()
    yield
    stop_scheduler()


settings = get_settings()
app = FastAPI(title="Groupify API", version="2.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(APIKeyMiddleware)

# ── Feature routers ──────────────────────────────────────────────────────────
app.include_router(assessment.router)
app.include_router(repo_judge.router)
app.include_router(project_suggest.router)
app.include_router(idea_validator.router)

# ── Automation routers (Options A, B, C) ─────────────────────────────────────
app.include_router(tasks.router)        # Option B: async task polling
app.include_router(webhooks.router)     # Option A: GitHub webhook receiver
app.include_router(automation.router)   # Option C: scheduler + skill-gap reports
