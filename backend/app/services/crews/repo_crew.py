import json
import logging

from crewai import Agent, Task

from backend.app.services.crews.base import parse_json_output, run_crew
from backend.app.services.llm_factory import extract_json_from_text, invoke_hybrid_llm
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


def run_repo_judge_crew(
    github_url: str,
    student_name: str,
    code_dump: str,
    static_summary: dict,
) -> dict:
    static_text = json.dumps(static_summary, indent=2)[:8000]

    code_analyst = Agent(
        role="Code Quality Analyst",
        goal="Evaluate structure, patterns, and coding style from static context",
        backstory="Staff engineer who reviews hackathon submissions.",
        allow_delegation=False,
    )
    security_agent = Agent(
        role="Security Reviewer",
        goal="Find secrets, unsafe patterns, and dependency risks",
        backstory="AppSec engineer focused on student projects.",
        allow_delegation=False,
    )
    mentor = Agent(
        role="Hackathon Judge & Mentor",
        goal="Synthesize scores and actionable mentor feedback as JSON",
        backstory="International hackathon judge with constructive tone.",
        allow_delegation=False,
    )

    t1 = Task(
        description=(
            f"Repository: {github_url}\nStudent: {student_name}\n"
            f"STATIC ANALYSIS (ruff/bandit):\n{static_text}\n\n"
            f"CODE SAMPLE:\n{code_dump[:25000]}\n\n"
            "Analyze code quality, architecture, documentation, coding style. "
            "Return bullet findings with file paths."
        ),
        expected_output="Structured analysis bullets with file paths",
        agent=code_analyst,
    )
    t2 = Task(
        description=(
            "Using the code sample and static analysis, list security issues and "
            "testing/CI gaps. Reference static tool output when available."
        ),
        expected_output="Security and testing findings",
        agent=security_agent,
        context=[t1],
    )
    t3 = Task(
        description=(
            "Merge prior analyses into ONE JSON object with keys: repo_url, accessibility, "
            "languages, scores (functionality, code_quality, documentation, architecture, "
            "testing_ci, innovation_ux — each score 0-10 with reasons), total_score, "
            "strengths, top_issues (objects with severity, title, description, files), "
            "security_warnings, reproducibility, mentor_notes, coding_style_summary "
            "(dedicated paragraph on naming, modularity, consistency). "
            f'Set repo_url to "{github_url}". Return ONLY JSON.'
        ),
        expected_output="Single JSON verdict object",
        agent=mentor,
        context=[t1, t2],
    )

    try:
        raw = run_crew([code_analyst, security_agent, mentor], [t1, t2, t3])
        result = parse_json_output(raw)
        if result and "scores" in result:
            result["repo_url"] = github_url
            result["student_name"] = student_name
            result["static_analysis"] = static_summary
            return result
    except Exception as e:
        logger.warning("Repo crew failed: %s", e)

    return _fallback_repo(github_url, student_name, code_dump, static_summary)


def _fallback_repo(github_url, student_name, code_dump, static_summary) -> dict:
    from backend.app.services.github_judge_service import analyze_repo_llm_only

    return analyze_repo_llm_only(github_url, student_name, code_dump, static_summary)
