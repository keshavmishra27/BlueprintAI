import json
import logging

from crewai import Agent, Task

from backend.app.services.crews.base import parse_json_output, run_crew
from backend.app.services.crews.tools import web_search_tool
from backend.app.services.search_service import search_for_idea

logger = logging.getLogger(__name__)


def run_idea_check_crew(idea: str, search_context: str, sources: list) -> dict:
    researcher = Agent(
        role="Market & Prior-Art Researcher",
        goal="Find similar products and open-source work with cited URLs",
        backstory="Startup analyst who never invents citations.",
        tools=[web_search_tool],
        allow_delegation=False,
    )
    analyst = Agent(
        role="Innovation Gap Analyst",
        goal="Map gaps vs competitors and assess novelty (not legal advice)",
        backstory="Product strategist focused on differentiation.",
        allow_delegation=False,
    )

    t1 = Task(
        description=(
            f"User idea:\n{idea}\n\n"
            f"LIVE SEARCH RESULTS (use these; cite URLs):\n{search_context}\n\n"
            "Use Web Search tool if results are thin. Return JSON with: similar_projects "
            "(name, type, overview, evidence with quote+url+date, comparison, relevance_score), "
            "gap_and_loopholes, search_queries_and_sources_used, notes_and_limitations. "
            "Do NOT claim patentability — this is market research only."
        ),
        expected_output="JSON market research report",
        agent=researcher,
    )
    t2 = Task(
        description=(
            "Refine the research into actionable gaps. Add patentability_assessment with "
            "disclaimer: 'Not legal advice — consult a patent attorney.' "
            "Output ONLY the full JSON schema from the researcher plus recommended_novel_modifications."
        ),
        expected_output="Complete JSON check result",
        agent=analyst,
        context=[t1],
    )

    try:
        raw = run_crew([researcher, analyst], [t1, t2])
        data = parse_json_output(raw)
        if data:
            data["search_sources"] = sources
            data.setdefault(
                "notes_and_limitations",
                "Automated web search; not a substitute for professional patent search.",
            )
            return data
    except Exception as e:
        logger.warning("Idea check crew failed: %s", e)
        return {
            "similar_projects": [],
            "search_sources": sources,
            "notes_and_limitations": f"Crew analysis failed: {e}",
        }

    return {
        "similar_projects": [],
        "search_sources": sources,
        "notes_and_limitations": "Crew returned empty output.",
    }


def run_idea_refine_crew(idea: str, check_result: dict) -> dict:
    refiner = Agent(
        role="Innovation Refinement Coach",
        goal="Score novelty dimensions and propose refined direction",
        backstory="Mentor helping students pivot ideas with evidence.",
        allow_delegation=False,
    )
    task = Task(
        description=(
            f"Idea:\n{idea}\n\nPrior research:\n{json.dumps(check_result, indent=2)[:12000]}\n\n"
            "Return JSON: uniqueness (verdict, matrix_scores, score, rationale), "
            "similar_projects_examined, loopholes, refined_concept, notes_and_limitations."
        ),
        expected_output="JSON refinement report",
        agent=refiner,
    )
    try:
        raw = run_crew([refiner], [task])
        data = parse_json_output(raw)
        if data:
            return data
    except Exception as e:
        logger.warning("Idea refine crew failed: %s", e)
        return {
            "uniqueness": {"verdict": "error", "score": 0, "rationale": str(e)},
            "loopholes": [],
            "refined_concept": {"final_direction": "Please retry."},
        }
    return {
        "uniqueness": {"verdict": "error", "score": 0, "rationale": "Empty crew output."},
        "loopholes": [],
        "refined_concept": {"final_direction": "Please retry."},
    }


def gather_idea_search(idea: str) -> tuple[list, str]:
    return search_for_idea(idea)
