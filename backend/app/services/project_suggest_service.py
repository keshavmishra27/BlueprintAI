"""
project_suggest_service.py
--------------------------
Given a theme / domain, asks the local Ollama LLM to return
structured JSON with:
  • 5 industry-grade resume project ideas
  • 5 hackathon-winning project ideas
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def suggest_projects(theme: str) -> dict:
    """
    Call Ollama to generate project suggestions for the given theme.
    Returns a dict with keys `resume_projects` and `hackathon_projects`.
    """
    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage

    system_prompt = (
        "You are an elite tech career mentor and hackathon judge with deep "
        "industry experience. When given a theme or domain, you return ONLY "
        "valid JSON — no markdown fences, no extra text."
    )

    user_prompt = f"""Generate project ideas for the theme: "{theme}"

Return ONLY this JSON object (no other text, no markdown):
{{
  "resume_projects": [
    {{
      "title": "<project title>",
      "description": "<2-3 sentence description of what it does>",
      "tech_stack": ["<tech1>", "<tech2>", "<tech3>"],
      "why_great_for_resume": "<1-2 sentences on why recruiters love this>"
    }}
  ],
  "hackathon_projects": [
    {{
      "title": "<project title>",
      "description": "<2-3 sentence description of what it does>",
      "tech_stack": ["<tech1>", "<tech2>", "<tech3>"],
      "why_it_wins": "<1-2 sentences on why judges pick this>"
    }}
  ]
}}

RULES:
- Provide exactly 5 items in resume_projects and 5 in hackathon_projects.
- Resume projects should be practical, industry-relevant, and demonstrate real engineering skills.
- Hackathon projects should be innovative, creative, demo-friendly, and have strong wow-factor.
- All projects must be original ideas, not generic tutorials.
- Tech stacks should be modern and specific.
- Return ONLY the JSON object, nothing else."""

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

    # Strip markdown fences if the model wraps them
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(raw)
        if "resume_projects" in data and "hackathon_projects" in data:
            return data
    except Exception:
        pass

    # Fallback when parsing fails
    return {
        "resume_projects": [
            {
                "title": "Could not parse — please retry",
                "description": raw[:300] if raw else "No response from model.",
                "tech_stack": [],
                "why_great_for_resume": "",
            }
        ],
        "hackathon_projects": [
            {
                "title": "Could not parse — please retry",
                "description": raw[:300] if raw else "No response from model.",
                "tech_stack": [],
                "why_it_wins": "",
            }
        ],
    }
