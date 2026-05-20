import json

from backend.app.services.crews.project_crew import run_project_suggest_crew


def suggest_projects(theme: str) -> dict:
    return run_project_suggest_crew(theme)


def suggest_projects_legacy(theme: str) -> dict:
    from backend.app.services.llm_factory import invoke_hybrid_llm
    from langchain_core.messages import SystemMessage, HumanMessage

    system_prompt = "Return JSON with resume_projects and hackathon_projects (5 each)."
    user_prompt = f"Theme: {theme}. Generate portfolio and hackathon project ideas."
    response = invoke_hybrid_llm(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
        temperature=0.7,
    )
    raw = response.content.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    try:
        data = json.loads(raw)
        if "resume_projects" in data and "hackathon_projects" in data:
            return data
    except Exception:
        pass
    return {
        "resume_projects": [{"title": "Retry", "description": raw[:300] if raw else "", "tech_stack": [], "why_great_for_resume": ""}],
        "hackathon_projects": [{"title": "Retry", "description": "", "tech_stack": [], "why_it_wins": ""}],
    }
