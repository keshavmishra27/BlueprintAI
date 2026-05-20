import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.config import get_settings
from backend.app.database import ensure_schema
from backend.app.middleware.auth import APIKeyMiddleware
from backend.app.middleware.rate_limit import limiter
from backend.app.routers import assessment, repo_judge, project_suggest, idea_validator, swot

logging.basicConfig(level=logging.INFO)

try:
    ensure_schema()
except Exception as e:
    logging.warning("Schema setup issue at startup: %s", e)

settings = get_settings()
app = FastAPI(title="Groupify API", version="2.0.0")
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
app.include_router(swot.router)
