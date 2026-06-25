import json
import logging
from crewai import Agent, Task
from backend.app.services.crews.base import parse_json_output, run_crew
from backend.app.services.llm_factory import extract_json_from_text, invoke_hybrid_llm
from backend.app.routers.repo_judge import JUDGE_JSON_SCHEMA, SCORING_RUBRIC
from langchain_core.messages import SystemMessage, HumanMessage
logger = logging.getLogger(__name__)
def _truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[...truncated due prompt size limit...]\n"
def run_repo_judge_crew(
    github_url: str,
    student_name: str,
    code_dump: str,
    static_summary: dict,
    repo_summary: str = "",
) -> dict:
    static_text = _truncate_text(json.dumps(static_summary, indent=2), 5000)
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
            f"REPO METADATA:\n{repo_summary}\n\n"
            f"STATIC ANALYSIS (ruff/bandit):\n{static_text}\n\n"
            f"CODE SAMPLE:\n{_truncate_text(code_dump, 12000)}\n\n"
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
            f"REPO METADATA:\n{repo_summary}\n\n"
            "Merge prior analyses into ONE JSON object. "
            "Return ONLY valid JSON — no markdown, no explanation, no extra text.\n\n"
            "CRITICAL TYPE RULES (violating these causes a system crash):\n"
            "- \"accessibility\" must be a STRING (e.g. \"public\"), never a dict\n"
            "- \"mentor_notes\" must be a STRING paragraph, never a list\n"
            "- \"coding_style_summary\" must be a STRING paragraph, never a list\n"
            "- Each score in \"scores\" must be an OBJECT with keys \"score\" (number), "
            "\"weight\" (number), and \"reasons\" (LIST of strings, never a single string)\n"
            "- \"reproducibility\" must be an OBJECT with \"can_run\" (bool), "
            "\"run_commands\" (list of strings), and \"notes\" (string)\n"
            "- \"files\" inside top_issues must be a list of OBJECTS with \"path\" and \"lines\" keys, "
            "never plain strings\n"
            "- \"hackathon_recommendations\" must be a list of OBJECTS suggesting 2-3 real-world upcoming or recurring corporate/global hackathons (e.g., MLH, specific company hackathons) where this project would be a great fit.\n\n"
            "Use the scoring rubric below to differentiate simple tutorial projects from full-stack or innovative solutions. "
            "Do not give every repo the same mid-range score.\n\n"
            f"{SCORING_RUBRIC}\n\n"
            f'Set repo_url to "{github_url}".\n\n'
            f"EXACT JSON SCHEMA TO FOLLOW:\n{JUDGE_JSON_SCHEMA}"
        ),
        expected_output="Single JSON verdict object matching the schema exactly",
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
    return _fallback_repo(github_url, student_name, code_dump, static_summary, repo_summary)
def _fallback_repo(github_url, student_name, code_dump, static_summary, repo_summary: str = "") -> dict:
    from backend.app.services.github_judge_service import analyze_repo_llm_only
    return analyze_repo_llm_only(
        github_url,
        student_name,
        code_dump,
        static_summary,
        repo_summary=repo_summary,
    )
