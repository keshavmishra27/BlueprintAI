import json
import math
from backend.app.services.crews.mcq_crew import run_mcq_crew
def generate_mcq(domain: str) -> list[dict]:
    questions = run_mcq_crew(domain)
    if questions:
        return questions
    return generate_mcq_legacy(domain)
def generate_mcq_legacy(domain: str) -> list[dict]:
    from backend.app.services.llm_factory import invoke_hybrid_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    system_prompt = """You are an expert technical interviewer.
Generate exactly 15 MCQs: 5 easy, 5 medium, 5 hard.
Each question: question, options (A-D), correct_answer (A|B|C|D), difficulty.
Return ONLY a valid JSON array."""
    user_prompt = f"Generate 15 scenario-based MCQs for domain: {domain}"
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
        questions = json.loads(raw)
        if isinstance(questions, list) and len(questions) >= 1:
            for q in questions:
                q.setdefault("difficulty", "medium")
                q.setdefault("correct_answer", "A")
                if not isinstance(q.get("options"), list) or len(q["options"]) < 4:
                    q["options"] = ["A) —", "B) —", "C) —", "D) —"]
            return questions
    except Exception:
        pass
    return [
        {
            "question": "The AI could not generate questions. Please try again.",
            "options": ["A) Retry", "B) Retry", "C) Retry", "D) Retry"],
            "correct_answer": "A",
            "difficulty": "easy",
        }
    ]
def grade_answers(questions: list[dict], answers: dict[str, str], db=None, domains=None, session_id=None) -> dict:
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
    weighted = easy_c * 1 + med_c * 2 + hard_c * 3
    max_weighted = easy_t * 1 + med_t * 2 + hard_t * 3
    percentile_info = {"percentile": 50, "percentile_source": "default", "cohort_size": 0, "message": ""}
    if db is not None:
        from backend.app.services.percentile_service import compute_real_percentile
        percentile_info = compute_real_percentile(
            db, domains or [], weighted, max_weighted, exclude_session_id=session_id
        )
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
        "percentile": percentile_info["percentile"],
        "percentile_source": percentile_info["percentile_source"],
        "cohort_size": percentile_info["cohort_size"],
        "percentile_message": percentile_info["message"],
        "details": details,
    }
