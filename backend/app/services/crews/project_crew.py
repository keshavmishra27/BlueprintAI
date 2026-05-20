import logging

from crewai import Agent, Task

from backend.app.services.crews.base import parse_json_output, run_crew
from backend.app.services.crews.tools import web_search_tool

logger = logging.getLogger(__name__)


def run_project_suggest_crew(theme: str) -> dict:
    resume_agent = Agent(
        role="Resume Project Mentor",
        goal="Design 5 FAANG-grade portfolio projects for the theme",
        backstory="Hiring manager who values measurable impact.",
        tools=[web_search_tool],
        allow_delegation=False,
    )
    hackathon_agent = Agent(
        role="Hackathon Coach",
        goal="Design 5 demo-ready hackathon winners",
        backstory="Judge who rewards novelty and clear demos.",
        allow_delegation=False,
    )

    t1 = Task(
        description=(
            f"Theme: {theme}\n"
            "Use Web Search to name 1-2 existing solutions per idea. "
            "Return JSON resume_projects: 5 items with title, description, tech_stack, "
            "why_great_for_resume."
        ),
        expected_output="JSON with resume_projects array",
        agent=resume_agent,
    )
    t2 = Task(
        description=(
            f"Theme: {theme}\n"
            "Return JSON hackathon_projects: 5 items with title, description, tech_stack, why_it_wins. "
            "Combine with resume_projects into one JSON object."
        ),
        expected_output="JSON with resume_projects and hackathon_projects",
        agent=hackathon_agent,
        context=[t1],
    )

    try:
        raw = run_crew([resume_agent, hackathon_agent], [t1, t2])
        data = parse_json_output(raw)
        if data.get("resume_projects") and data.get("hackathon_projects"):
            return data
    except Exception as e:
        logger.warning("Project crew failed: %s", e)

    from backend.app.services.project_suggest_service import suggest_projects_legacy

    return suggest_projects_legacy(theme)
