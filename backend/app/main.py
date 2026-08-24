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
from backend.app.routers import tasks, webhooks, automation, journey
logging.basicConfig(level=logging.INFO)
try:
    ensure_schema()
except Exception as e:
    logging.warning("Schema setup issue at startup: %s", e)
def _register_task_handlers():
    from backend.app.services.task_queue import register_handler
    from backend.app.routers.webhooks import _handle_webhook_repo_judge
    from backend.app.services.scheduler import run_skill_gap_job
    register_handler("webhook_repo_judge", _handle_webhook_repo_judge)
    register_handler("skill_gap_analysis", lambda _payload: run_skill_gap_job() or {})
_register_task_handlers()
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
app.include_router(assessment.router)
app.include_router(repo_judge.router)
app.include_router(project_suggest.router)
app.include_router(idea_validator.router)
app.include_router(tasks.router)        
app.include_router(webhooks.router)     
app.include_router(automation.router)   
app.include_router(journey.router)

from product.api.v1.routes import router as product_router
app.include_router(product_router, prefix="/api/v1", tags=["Product"])
