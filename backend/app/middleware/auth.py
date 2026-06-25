from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.config import get_settings
PUBLIC_PATHS = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/assess/domains",
    "/repo-judge/health",
    "/project-suggest/health",
    "/idea-validator/health",
    "/webhooks/health",
    "/webhooks/github",       
    "/tasks/health",
    "/automation/health",
}
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not settings.api_key:
            return await call_next(request)
        path = request.url.path.rstrip("/") or "/"
        if path in PUBLIC_PATHS or path.startswith("/docs"):
            return await call_next(request)
        provided = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
        if provided != settings.api_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key.")
        return await call_next(request)
