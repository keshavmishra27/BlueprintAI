from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from ..services.idea_validator_service import check_similar_ideas, refine_idea

router = APIRouter(prefix="/idea-validator", tags=["Idea Validator"])

class IdeaRequest(BaseModel):
    idea: str

@router.post("/check")
async def check_idea(req: IdeaRequest):
    if not req.idea.strip():
        raise HTTPException(status_code=400, detail="Idea cannot be empty")
    return check_similar_ideas(req.idea)

@router.post("/refine")
async def post_refine_idea(req: IdeaRequest):
    if not req.idea.strip():
        raise HTTPException(status_code=400, detail="Idea cannot be empty")
    
    # First get similar ideas to provide context for refinement
    # Note: check_similar_ideas already returns the rich JSON schema with similar_projects
    similar = check_similar_ideas(req.idea)
    return refine_idea(req.idea, similar.get("similar_projects", []))
