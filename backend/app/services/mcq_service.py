import os
import json
import math
from dotenv import load_dotenv
load_dotenv()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
def generate_mcq(domain: str) -> list[dict]:
    from .llm_factory import invoke_hybrid_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    system_prompt = """You are an expert technical interviewer and subject matter expert.
    Your task is to generate 15 high-quality multiple-choice questions (MCQs) for a specific technical domain.
    The questions must be divided exactly as follows:
    - 5 Easy questions: Testing basic concepts and syntax.
    - 5 Medium questions: Testing logic, integration, and common libraries.
    - 5 Hard questions: Testing architecture, edge cases, and performance optimization.
    Each question must have:
    - A clear question statement.
    - 4 distinct options labeled A, B, C, D.
    - The correct answer letter (A, B, C, or D).
    - The assigned difficulty.
    Return ONLY a valid JSON list of objects."""
    user_prompt = f"""You are a subject-matter MCQ generator. Given a domain string {domain} (replace this placeholder with the actual domain, e.g., "networking", "data science", "manufacturing"), produce 15 technical, scenario-based multiple-choice questions that evaluate a student’s ability to apply domain knowledge to realistic, productivity-focused situations (decision making, prioritization, troubleshooting, optimization, time/resource tradeoffs), not just recall facts.
Output format (required) — Return ONLY this JSON array (no commentary, no extra text):
[
{{
"question": "short scenario + stem",
"options": ["A) ...", "B) ...", "C) ...", "D) ..."],
"correct_answer": "A",
"difficulty": "easy"
}},
...
]
(15 objects total)
Question-writing rules
Each item must be self-contained. Begin with a concise scenario (≤35 words), then a clear question stem asking for the best action, likely outcome, or best explanation in that scenario. Total length ≲2 sentences.
Focus on application/productivity: prefer "what will you do next?", "which choice maximizes throughput/minimizes downtime?", "which action best mitigates risk under these constraints?", "which sequence optimizes output given X?", or small calculations that measure effectiveness.
Use real-world constraints (time, cost, resources, deadlines, system capacity). If numeric reasoning is required, include all numbers and units needed to solve it.
Include a mix of cognitive skills: prioritization, troubleshooting, root-cause identification, small calculations, tool-selection, trade-off analysis, and best-next-step decisions.
Avoid pure memorization questions (no definitions-only recall).
Difficulty distribution: 6 easy, 6 medium, 3 hard.
easy: basic applied decisions or simple one-step calculations.
medium: multi-step reasoning or comparing tradeoffs.
hard: require combining concepts, multi-stage planning, or nontrivial calculations.
Options: always four options labeled exactly as "A) ...", "B) ...", "C) ...", "D) ...".
Keep each option concise (≤20 words).
Make distractors plausible and domain-relevant.
Do not use "All of the above" or "None of the above."
Ensure there is one clearly best answer (no ties or ambiguous best choices).
correct_answer must be a single uppercase letter "A", "B", "C", or "D".
difficulty must be one of "easy", "medium", or "hard".
Cover a variety of subtopics across {domain} so the 15 questions are diverse.
Language: concise, precise, professional; avoid slang and vague phrasing.
Ensure JSON is valid UTF-8 and parsable.
Example scenario templates (do not output examples in final result; these are guidelines for question style):
“You have 4 tasks and 2 engineers; task A is blocking others and has highest ROI. Which do you assign first?”
“A server shows CPU at 95% while response time doubles; which immediate action best restores throughput?”
“Given these throughput numbers and a bottleneck stage, which optimization yields largest end-to-end gain?”
Now generate 15 questions for the domain {domain} following the rules above and return EXACTLY the JSON array described."""
    response = invoke_hybrid_llm([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ], temperature=0.7)
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
def grade_answers(questions: list[dict], answers: dict[str, str]) -> dict:
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
    if max_weighted == 0:
        return 50
    ratio = weighted / max_weighted
    k = 10
    raw = 1.0 / (1.0 + math.exp(-k * (ratio - 0.5)))
    percentile = int(2 + raw * 97)
    return min(99, max(1, percentile))