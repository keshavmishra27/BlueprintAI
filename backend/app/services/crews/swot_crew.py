import logging

from crewai import Agent, Task

from backend.app.services.crews.base import parse_json_output, run_crew
from backend.app.services.crews.tools import web_search_tool

logger = logging.getLogger(__name__)


def run_swot_crew(
    subject_name: str,
    subject_type: str,
    description: str,
) -> dict:
    strategist = Agent(
        role="SWOT Strategist",
        goal="Produce evidence-based SWOT for projects or product ideas",
        backstory="Management consultant for early-stage tech ventures.",
        tools=[web_search_tool],
        allow_delegation=False,
    )
    critic = Agent(
        role="Strategic Reviewer",
        goal="Validate SWOT balance and add prioritized action items",
        backstory="Ensures SWOT is specific, not generic buzzwords.",
        allow_delegation=False,
    )

    t1 = Task(
        description=(
            f"Subject: {subject_name}\nType: {subject_type}\nDescription:\n{description}\n\n"
            "Use Web Search for market/competitor context when helpful. "
            "Return JSON: strengths, weaknesses, opportunities, threats (each a list of "
            "objects with title, detail, evidence_or_assumption), strategic_recommendations "
            "(priority 1-3 actions), and notes."
        ),
        expected_output="SWOT JSON object",
        agent=strategist,
    )
    t2 = Task(
        description="Review and finalize the SWOT JSON. Ensure at least 3 items per quadrant.",
        expected_output="Final SWOT JSON",
        agent=critic,
        context=[t1],
    )

    try:
        raw = run_crew([strategist, critic], [t1, t2])
        data = parse_json_output(raw)
        if data and "strengths" in data:
            data["subject_name"] = subject_name
            data["subject_type"] = subject_type
            return data
    except Exception as e:
        logger.warning("SWOT crew failed: %s", e)

    return {
        "strengths": [],
        "weaknesses": [],
        "opportunities": [],
        "threats": [],
        "strategic_recommendations": [],
        "notes": f"SWOT analysis failed: {e}",
        "subject_name": subject_name,
        "subject_type": subject_type,
    }
