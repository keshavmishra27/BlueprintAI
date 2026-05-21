"""
Option C – Skill-Gap Curator crew.

A CrewAI crew that analyses all recent assessment scores and repo-judge
results in the database, identifies skill gaps, and recommends tailored
project ideas + learning paths for each student.
"""

import json
import logging

from crewai import Agent, Task

from backend.app.services.crews.base import parse_json_output, run_crew

logger = logging.getLogger(__name__)


def run_skill_gap_crew(student_summaries: list[dict]) -> dict:
    """
    Parameters
    ----------
    student_summaries : list[dict]
        Each dict has: student_name, domains, avg_score, repo_scores,
        weakest_domain, strongest_domain.

    Returns
    -------
    dict with keys: students (list of gap analyses), overall_insights, timestamp.
    """
    summaries_text = json.dumps(student_summaries, indent=2)[:15000]

    analyst = Agent(
        role="Skill-Gap Analyst",
        goal="Identify concrete skill gaps by comparing quiz and repo scores",
        backstory=(
            "Data-driven HR analyst who maps competency gaps to actionable "
            "upskilling plans. Never gives vague advice."
        ),
        allow_delegation=False,
    )
    curator = Agent(
        role="Project Curator & Learning Coach",
        goal="Recommend targeted mini-projects and resources for each gap",
        backstory=(
            "Senior engineering mentor who matches students to projects that "
            "close specific skill gaps. Suggests concrete repos to study."
        ),
        allow_delegation=False,
    )

    t1 = Task(
        description=(
            f"Here are the student performance summaries:\n{summaries_text}\n\n"
            "For EACH student, identify:\n"
            "- weakest_areas (specific topics, not just domain names)\n"
            "- strength_areas\n"
            "- gap_score (0-100, higher = bigger gap)\n"
            "Return JSON: { students: [{student_name, weakest_areas, "
            "strength_areas, gap_score}], overall_patterns: [...] }"
        ),
        expected_output="JSON with per-student gap analysis",
        agent=analyst,
    )
    t2 = Task(
        description=(
            "For each student's gaps from the previous analysis, recommend:\n"
            "- 2 targeted mini-project ideas (title, description, tech_stack, "
            "which_gap_it_closes)\n"
            "- 1 open-source repo to study\n"
            "- 1 learning resource (blog/course/docs)\n\n"
            "Merge with the gap analysis into ONE JSON:\n"
            "{ students: [{student_name, gaps, recommendations}], "
            "overall_insights: str }"
        ),
        expected_output="Complete JSON skill-gap report with recommendations",
        agent=curator,
        context=[t1],
    )

    try:
        raw = run_crew([analyst, curator], [t1, t2])
        data = parse_json_output(raw)
        if data and "students" in data:
            return data
    except Exception as e:
        logger.warning("Skill-gap crew failed: %s", e)

    return {
        "students": [],
        "overall_insights": "Skill-gap analysis could not be completed.",
        "error": True,
    }
