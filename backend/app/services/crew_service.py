import os
import json
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"


def _get_llm():
    """Configure CrewAI to use Ollama via its OpenAI-compatible endpoint."""
    from crewai import LLM
    return LLM(
        model=OLLAMA_MODEL,
        base_url=f"{OLLAMA_BASE_URL}/v1",
        api_key="ollama",  
    )



def get_interviewer_response(
    student_name: str,
    domains: list[str],
    conversation_history: list[dict],
    student_message: str,
) -> str:
    """
    Stateful chat with the interviewer agent using Ollama locally.
    """
    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

    domains_str = ", ".join(domains) if domains else "General"

    system_prompt = f"""You are an expert academic interviewer assessing a student named {student_name}.

The student has selected the following domain(s): {domains_str}.

Your job:
- Ask intelligent, domain-specific questions to evaluate their knowledge and thinking ability
- Probe deeper when they give interesting answers
- Assess creativity by asking "what if" or "how would you approach" type questions
- Keep the conversation natural and encouraging, not intimidating
- Ask one question at a time
- Keep your responses concise (2-3 sentences max)
- After they answer, either follow up or move to a new aspect of the domain

You are evaluating them on:
1. Domain knowledge accuracy
2. Creativity and original thinking
3. Communication clarity
4. Depth of engagement

Start by introducing yourself briefly and asking the first domain-specific question."""

    messages = [SystemMessage(content=system_prompt)]
    for turn in conversation_history:
        if turn["role"] == "student":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=student_message))

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.7,
    )
    response = llm.invoke(messages)
    return response.content



def score_session(
    student_name: str,
    domains: list[str],
    conversation_history: list[dict],
) -> dict:
    """
    Analyze the full conversation transcript with a single Ollama LLM call.
    Returns a dict with dimension scores + overall feedback.
    """
    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage

    domains_str = ", ".join(domains) if domains else "General"

    transcript = "\n".join(
        f"{'STUDENT' if t['role'] == 'student' else 'INTERVIEWER'}: {t['content']}"
        for t in conversation_history
    )

    system_prompt = """You are an expert academic evaluator. Analyze interview conversations and return ONLY valid JSON with no other text."""

    user_prompt = f"""Evaluate student {student_name}'s performance in this interview about {domains_str}.

TRANSCRIPT:
{transcript}

Return ONLY this JSON object (no other text, no markdown):
{{
  "domain_knowledge": <integer 0-25>,
  "creativity": <integer 0-25>,
  "communication": <integer 0-25>,
  "engagement": <integer 0-25>,
  "total": <integer 0-100>,
  "summary": "<2-3 sentence overall feedback>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "areas_to_improve": ["<area 1>", "<area 2>"]
}}"""

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.3,   
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    raw = response.content.strip()

    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        scores = json.loads(raw)
        required = ["domain_knowledge", "creativity", "communication", "engagement", "total", "summary"]
        if all(k in scores for k in required):
            scores["total"] = (
                scores["domain_knowledge"] +
                scores["creativity"] +
                scores["communication"] +
                scores["engagement"]
            )
            return scores
    except Exception:
        pass

    return {
        "domain_knowledge": 15,
        "creativity": 15,
        "communication": 15,
        "engagement": 15,
        "total": 60,
        "summary": raw[:500] if raw else "Assessment complete.",
        "strengths": ["Participated in the assessment"],
        "areas_to_improve": ["Could not parse detailed scores — please retry"],
    }
