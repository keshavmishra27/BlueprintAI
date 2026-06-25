from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.middleware.rate_limit import limiter
from backend.app.models import IdeaValidation
from ..services.idea_validator_service import check_similar_ideas, refine_idea
from ..services.llm_factory import check_llm_availability
router = APIRouter(prefix="/idea-validator", tags=["Idea Validator"])
class IdeaRequest(BaseModel):
    idea: str
@router.get("/health")
def health():
    return {"status": "ok", "route": "/idea-validator"}
@router.post("/check")
@limiter.limit("5/minute")
def check_idea(request: Request, req: IdeaRequest, db: Session = Depends(get_db)):
    if not req.idea.strip():
        raise HTTPException(status_code=400, detail="Idea cannot be empty")
    check_llm_availability()
    result = check_similar_ideas(req.idea)
    row = IdeaValidation(
        idea_text=req.idea.strip(),
        check_result_json=result,
        search_sources_json=result.get("search_sources"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    result["validation_id"] = row.id
    return result
@router.post("/refine")
@limiter.limit("5/minute")
def post_refine_idea(request: Request, req: IdeaRequest, db: Session = Depends(get_db)):
    if not req.idea.strip():
        raise HTTPException(status_code=400, detail="Idea cannot be empty")
    check_llm_availability()
    similar = check_similar_ideas(req.idea)
    refined = refine_idea(req.idea, similar.get("similar_projects", []))
    row = IdeaValidation(
        idea_text=req.idea.strip(),
        check_result_json=similar,
        refine_result_json=refined,
        search_sources_json=similar.get("search_sources"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    refined["validation_id"] = row.id
    return refined
