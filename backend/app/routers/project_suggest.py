import os
from typing import List
import requests as http_requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
router = APIRouter(prefix="/project-suggest", tags=["Project Suggest"])
from ..services.llm_factory import check_llm_availability
class SuggestRequest(BaseModel):
    themes: List[str]
class ProjectItem(BaseModel):
    title: str = ""
    description: str = ""
    tech_stack: List[str] = []
    why_great_for_resume: str = ""
    why_it_wins: str = ""
class SuggestResult(BaseModel):
    themes: List[str]
    resume_projects: List[ProjectItem] = []
    hackathon_projects: List[ProjectItem] = []
@router.get("/health", summary="Project Suggest health check")
def health():
    return {"status": "ok", "route": "/project-suggest"}
@router.post(
    "/suggest",
    response_model=SuggestResult,
    summary="Get AI-powered project suggestions for a theme",
    description=(
        """You are an expert mentor and product designer tasked with generating resume-grade projects and hackathon winners for students.
Input: a single theme/domain string (examples: "AI", "FinTech", "Healthcare", "DSA", "EdTech").
Goal: produce **5 industry-grade resume project ideas** and **5 hackathon-winning project ideas** that are original, feasible, and solve concrete real-world problems or fix notable shortcomings in existing solutions. Each idea must include evidence of novelty (explicitly name 1–3 existing projects/products and describe their limitations), step-by-step MVP plan, success metrics, a realistic tech stack, data plan, demo script, estimated time & team size, and a short mentorship checklist.
Output format: produce TWO artifacts in the same response:
A) Machine-friendly JSON (first) following the schema below.
B) A human-friendly markdown summary (second) — one paragraph per idea, highlighting top reasons a mentor would pick this project for grading or hackathon submission.
A) JSON schema (required keys)
{
  "theme":"<input theme>",
  "resume_projects":[
    {
      "id":"rp1",
      "title":"Short title",
      "tagline":"1-line hook",
      "problem_statement":"Concrete problem + who suffers + scale",
      "existing_solutions":["name + 1-line limit each"],
      "gap_analysis":"Exactly what is missing in existing solutions (2-3 bullet points)",
      "unique_value_proposition":"Why this idea solves the gap",
      "mvp_spec":{
         "core_features":["feature list for MVP (3-6 items)"],
         "nonfunctional":["performance/latency/privacy/scale targets if relevant"]
      },
      "data_and_datasets":{
         "public_sources":["list public datasets/APIs with exact names"],
         "synthetic_plan":"if data is not public, how to synthesize or collect quickly"
      },
      "tech_stack":{"frontend":"", "backend":"", "models":"", "db":"", "infra":""},
      "deliverables_for_resume":["what to include in README/portfolio/demo video/metrics"],
      "mentorship_checklist":["code quality standards","tests to include","docs to have"],
      "success_metrics":["2-4 measurable KPIs to show impact"],
      "time_and_scope":{"team_size":int,"difficulty":"easy|medium|hard","estimated_hours":int}
    }, ...
  ],
  "hackathon_projects":[
    {
      "id":"hh1",
      "title":"Short title",
      "elevator_pitch":"1-liner",
      "killer_demo_script":"Step-by-step 60-90s demo script (what the judges see and the data shown)",
      "problem_statement":"real gap + why judges should care",
      "existing_solutions":["1-3 names"],
      "novelty":"concrete technical or UX novelty (1-3 bullets)",
      "mvp_components":["3-6 minimum components to implement during the hackathon"],
      "quick_win_implementation_plan":{
         "first_4_hours":"what to wire up first",
         "next_6_hours":"what to build next",
         "final_polish":"what to add for demo"
      },
      "tech_stack":["recommended stack to finish fast"],
      "winning_tips":["how to present impact/metrics, how to handle Q&A, advisor/dataset fallbacks"],
      "stretch_goals":["nice-to-have features for judges' bonus points"],
      "time_and_scope":{"team_size":int,"hackathon_hours":int}
    }, ...
  ],
  "novelty_constraints":"For every idea, the agent MUST explicitly name at least one existing project/product and then state 2–3 concrete ways the proposed idea is different and why it matters.",
  "ethical_and_privacy_notes":"If the idea uses personal data/biometric/financial data, include a short privacy mitigation strategy and consent checklist.",
  "evaluation_rubric":{
    "impact":{"weight":0.35,"criteria":"measurable benefit to users or organizations"},
    "feasibility":{"weight":0.25,"criteria":"completable by students with given time/resources"},
    "novelty":{"weight":0.20,"criteria":"clearly closes a gap vs named existing solutions"},
    "demo_and_polish":{"weight":0.20,"criteria":"stage-ready UX, reproducible demo, metrics shown"}
  },
  "examples_and_templates":{
    "resume_bullet_template":"One short example bullet students can paste into resume showing measurable outcome",
    "hackathon_presentation_template":"5-sentence template for pitch + 3 data slides to include"
  }
}
Behavioral rules and constraints:
1. Never suggest using private or paid-only datasets without providing a free alternative or a synthetic-data plan.
2. Do not recommend projects that are obvious clones of popular repos/apps. If concept is similar, explicitly describe the improvement or pivot.
3. For AI/model-heavy ideas, recommend specific open-source models or hosted APIs, and indicate approximate compute needs (CPU/GPU).
4. Keep ideas focused: each resume project should be completable by 1–3 students in the estimated hours; each hackathon idea should be completable in the given hackathon_hours.
5. Provide at least one measurable KPI for each idea.
6. Use plain language; no marketing fluff.
"""
    ),
)
def suggest_projects(req: SuggestRequest):
    if not req.themes:
        raise HTTPException(status_code=400, detail="themes list cannot be empty.")
    theme_str = ", ".join([t.strip() for t in req.themes if t.strip()])
    if not theme_str:
        raise HTTPException(status_code=400, detail="no valid themes provided.")
    check_llm_availability()
    from ..services.project_suggest_service import suggest_projects as run_suggest
    try:
        data = run_suggest(theme=theme_str)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Suggestion failed: {e}",
        )
    # Normalise into ProjectItem-compatible dicts
    resume = []
    for p in data.get("resume_projects", []):
        if isinstance(p, dict):
            resume.append(ProjectItem(**{k: p.get(k, "") for k in ProjectItem.model_fields}).dict())
    hackathon = []
    for p in data.get("hackathon_projects", []):
        if isinstance(p, dict):
            hackathon.append(ProjectItem(**{k: p.get(k, "") for k in ProjectItem.model_fields}).dict())
    # Return as dict for robustness.
    # Frontend expects 'theme' (singular) often, so we provide both for safety.
    return {
        "themes": req.themes,
        "theme": theme_str,
        "resume_projects": resume,
        "hackathon_projects": hackathon,
    }