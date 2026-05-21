import json
import logging

from crewai import Agent, Task

from backend.app.services.crews.base import parse_json_output, run_crew
from backend.app.services.crews.tools import web_search_tool
from backend.app.services.search_service import search_for_idea

logger = logging.getLogger(__name__)


IDEA_CHECK_SCHEMA = """\
{
  "similar_projects": [
    {
      "name": "Project Name",
      "type": "open-source tool",
      "overview": "Brief description of the project.",
      "evidence": [
        {"quote": "Exact quote from source", "source_url": "https://example.com", "date": "2024-01-15"}
      ],
      "comparison": "How this compares to the user's idea.",
      "relevance_score": 75
    }
  ],
  "gap_and_loopholes": "Paragraph describing gaps in the market.",
  "search_queries_and_sources_used": ["query 1", "query 2"],
  "notes_and_limitations": "Paragraph about limitations of this research."
}"""

IDEA_REFINE_SCHEMA = """\
{
  "uniqueness": {
    "verdict": "moderately_unique",
    "score": 65,
    "rationale": "Paragraph explaining the uniqueness assessment."
  },
  "similar_projects_examined": ["Project A", "Project B"],
  "loopholes": [
    {
      "issue": "Short title of the gap",
      "description": "Detailed description of the gap.",
      "proposed_solution": {
        "short": "One-line fix summary",
        "technical_details": "Detailed technical explanation of the fix.",
        "dev_effort_hours": 8
      }
    }
  ],
  "refined_concept": {
    "final_direction": "Paragraph describing the recommended pivot direction.",
    "quick_win_variant": {"description": "Easy-to-implement version."},
    "high_diff_variant": {"description": "Maximum differentiation version."}
  },
  "recommended_novel_modifications": [
    {
      "short_title": "Feature name",
      "technical_description": "What to build and why it's novel.",
      "potential_claims_legal_style": ["Claim 1 text"]
    }
  ],
  "patentability_assessment": {
    "novelty_summary": "Assessment of novelty.",
    "inventive_step_summary": "Assessment of inventive step.",
    "industrial_applicability": "Assessment of applicability.",
    "blocking_prior_art": [{"patent_id": "US1234567", "summary": "Brief summary"}]
  },
  "implementation_plan_high_level": {
    "milestones": [
      {"name": "MVP", "duration_days": 14, "tasks": ["task 1", "task 2"]}
    ]
  },
  "notes_and_limitations": "Paragraph about limitations."
}"""


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
            "Use Web Search tool if results are thin. Return ONLY valid JSON.\n\n"
            "CRITICAL TYPE RULES (violating these causes a system crash):\n"
            "- \"evidence\" MUST be a LIST of objects, each with \"quote\" (string), "
            "\"source_url\" (string), \"date\" (string). NEVER a plain string.\n"
            "- \"similar_projects\" MUST be a LIST of objects. NEVER a plain string.\n"
            "- \"relevance_score\" must be a NUMBER (0-100), not a string.\n\n"
            "Do NOT claim patentability — this is market research only.\n\n"
            f"EXACT JSON SCHEMA TO FOLLOW:\n{IDEA_CHECK_SCHEMA}"
        ),
        expected_output="JSON market research report matching the schema exactly",
        agent=researcher,
    )
    t2 = Task(
        description=(
            "Refine the research into actionable gaps. Add patentability_assessment with "
            "disclaimer: 'Not legal advice — consult a patent attorney.' "
            "Output ONLY the full JSON schema from the researcher plus recommended_novel_modifications.\n\n"
            "CRITICAL: All type rules from the previous task MUST be preserved."
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
            "Return ONLY valid JSON — no markdown, no explanation, no extra text.\n\n"
            "CRITICAL TYPE RULES (violating these causes a system crash):\n"
            "- \"loopholes\" MUST be a LIST of OBJECTS. Each object MUST have:\n"
            "  \"issue\" (string), \"description\" (string), and \"proposed_solution\" (OBJECT with "
            "\"short\" (string), \"technical_details\" (string), \"dev_effort_hours\" (number))\n"
            "- \"uniqueness\" MUST be an OBJECT with \"verdict\" (string), \"score\" (number), \"rationale\" (string)\n"
            "- \"refined_concept\" MUST be an OBJECT with \"final_direction\" (string)\n"
            "- \"recommended_novel_modifications\" MUST be a LIST of OBJECTS\n"
            "- \"implementation_plan_high_level.milestones\" MUST be a LIST of OBJECTS\n"
            "- NEVER return a plain string where a list or object is expected\n\n"
            f"EXACT JSON SCHEMA TO FOLLOW:\n{IDEA_REFINE_SCHEMA}"
        ),
        expected_output="JSON refinement report matching the schema exactly",
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
