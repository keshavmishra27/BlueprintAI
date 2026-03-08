"""
mcq_service.py
--------------
Generates 15 MCQ questions (5 easy, 5 medium, 5 hard) for a given domain
using the local Ollama LLM, and computes a developer-percentile from the score.
"""

import os
import json
import math
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def generate_mcq(domain: str) -> list[dict]:
    """
    Ask Ollama to produce 15 MCQs for *domain*.
    Returns a list of dicts, each with:
        question, options (list of 4), correct_answer, difficulty
    """
    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage

    system_prompt = (
        "You are an expert technical quiz creator. "
        "Return ONLY valid JSON — no markdown fences, no extra text."
    )

    user_prompt = f"""Create exactly 15 multiple-choice questions about the following domain(s): "{domain}".
CRITICAL REQUIREMENT: These must NOT be theoretical or bookish questions. Instead, create REAL-LIFE SCENARIOS that test a developer's practical problem-solving skills, debugging, architecture, and productivity.

Difficulty distribution:
- Questions 1-5: EASY (common practical scenarios a beginner should safely handle)
- Questions 6-10: MEDIUM (intermediate scenarios involving trade-offs, debugging, or real-world constraints)
- Questions 11-15: HARD (complex production issues, tricky edge cases, or advanced architecture choices)

Return ONLY this JSON array (no other text):
[
  {{
    "question": "<question text>",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": "A",
    "difficulty": "easy"
  }}
]

RULES:
- Exactly 15 items: 5 easy, 5 medium, 5 hard.
- correct_answer must be one of "A", "B", "C", "D".
- Each option string must start with "A) ", "B) ", "C) ", "D) ".
- Questions must be specific, technical, and unambiguous.
- Return ONLY the JSON array."""

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.7,
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    raw = response.content.strip()

    # Strip markdown fences
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        questions = json.loads(raw)
        if isinstance(questions, list) and len(questions) >= 1:
            # Normalise each question
            for q in questions:
                q.setdefault("difficulty", "medium")
                q.setdefault("correct_answer", "A")
                if not isinstance(q.get("options"), list) or len(q["options"]) < 4:
                    q["options"] = ["A) —", "B) —", "C) —", "D) —"]
            return questions
    except Exception:
        pass

    # Fallback – single error question so the UI can still render
    return [
        {
            "question": "The AI could not generate questions. Please try again.",
            "options": ["A) Retry", "B) Retry", "C) Retry", "D) Retry"],
            "correct_answer": "A",
            "difficulty": "easy",
        }
    ]


def grade_answers(questions: list[dict], answers: dict[str, str]) -> dict:
    """
    Grade user answers against the question list.

    Parameters
    ----------
    questions : list of question dicts (with correct_answer)
    answers   : dict mapping question index (str) → chosen letter ("A"–"D")

    Returns
    -------
    dict with:
        total, correct, wrong,
        easy_correct, easy_total, medium_correct, medium_total,
        hard_correct, hard_total,
        percentile, details (per-question breakdown)
    """

    easy_c = easy_t = med_c = med_t = hard_c = hard_t = 0
    details = []

    for i, q in enumerate(questions):
        chosen = answers.get(str(i), "")
        correct = q.get("correct_answer", "")
        is_correct = chosen.upper() == correct.upper()

        diff = q.get("difficulty", "medium").lower()
        if diff == "easy":
            easy_t += 1
            if is_correct:
                easy_c += 1
        elif diff == "hard":
            hard_t += 1
            if is_correct:
                hard_c += 1
        else:
            med_t += 1
            if is_correct:
                med_c += 1

        details.append({
            "index": i,
            "question": q.get("question", ""),
            "options": q.get("options", []),
            "correct_answer": correct,
            "user_answer": chosen,
            "is_correct": is_correct,
            "difficulty": diff,
        })

    total = len(questions)
    correct = easy_c + med_c + hard_c

    # Weighted score: easy=1pt, medium=2pt, hard=3pt
    weighted = easy_c * 1 + med_c * 2 + hard_c * 3
    max_weighted = easy_t * 1 + med_t * 2 + hard_t * 3
    percentile = compute_percentile(weighted, max_weighted)

    return {
        "total": total,
        "correct": correct,
        "wrong": total - correct,
        "easy_correct": easy_c,
        "easy_total": easy_t,
        "medium_correct": med_c,
        "medium_total": med_t,
        "hard_correct": hard_c,
        "hard_total": hard_t,
        "weighted_score": weighted,
        "max_weighted": max_weighted,
        "percentile": percentile,
        "details": details,
    }


def compute_percentile(weighted: int, max_weighted: int) -> int:
    """
    Map a weighted score to a developer percentile (0-99).
    Uses a sigmoid-like curve so that:
        0  correct → ~5%
        half correct → ~50%
        all correct → ~99%
    """
    if max_weighted == 0:
        return 50
    ratio = weighted / max_weighted          # 0.0 → 1.0
    # Logistic curve: 1 / (1 + e^(-k*(x - 0.5)))
    k = 10
    raw = 1.0 / (1.0 + math.exp(-k * (ratio - 0.5)))
    # Scale to 2–99 range
    percentile = int(2 + raw * 97)
    return min(99, max(1, percentile))
