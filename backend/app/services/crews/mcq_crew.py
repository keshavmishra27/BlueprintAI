import json
import logging

from crewai import Agent, Task

from backend.app.services.crews.base import parse_json_list_output, run_crew
from backend.app.services.llm_factory import invoke_hybrid_llm, extract_json_from_text
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

MCQ_SPEC = (
    "Generate exactly 15 MCQs: 5 easy, 5 medium, 5 hard. "
    "Each has question, options (A-D), correct_answer (A|B|C|D), difficulty."
)


def run_mcq_crew(domain: str) -> list[dict]:
    writer = Agent(
        role="Technical MCQ Author",
        goal=f"Write 15 scenario-based MCQs for domain: {domain}",
        backstory="Expert interviewer who tests applied skills, not memorization.",
        allow_delegation=False,
    )
    reviewer = Agent(
        role="Assessment Quality Reviewer",
        goal="Validate MCQ JSON is complete, balanced 5/5/5, and fix any gaps",
        backstory="EdTech QA lead ensuring fair, unambiguous exams.",
        allow_delegation=False,
    )
    write_task = Task(
        description=(
            f"{MCQ_SPEC}\nDomain: {domain}\n"
            "Return ONLY a JSON array of 15 objects with keys: "
            "question, options, correct_answer, difficulty."
        ),
        expected_output="JSON array of 15 MCQ objects",
        agent=writer,
    )
    review_task = Task(
        description=(
            "Review the MCQs from the previous task. Fix duplicates, ambiguous answers, "
            "or wrong difficulty counts. Output ONLY the final JSON array."
        ),
        expected_output="Validated JSON array of 15 MCQs",
        agent=reviewer,
        context=[write_task],
    )
    try:
        raw = run_crew([writer, reviewer], [write_task, review_task])
        questions = parse_json_list_output(raw)
        if questions:
            return _normalize_questions(questions)
    except Exception as e:
        logger.warning("MCQ crew failed, using LLM fallback: %s", e)

    return _fallback_mcq(domain)


def _normalize_questions(questions: list) -> list[dict]:
    out = []
    for q in questions[:15]:
        if not isinstance(q, dict):
            continue
        q.setdefault("difficulty", "medium")
        q.setdefault("correct_answer", "A")
        if not isinstance(q.get("options"), list) or len(q["options"]) < 4:
            q["options"] = ["A) —", "B) —", "C) —", "D) —"]
        out.append(q)
    return out if out else []


def _fallback_mcq(domain: str) -> list[dict]:
    from backend.app.services.mcq_service import generate_mcq_legacy

    return generate_mcq_legacy(domain)
