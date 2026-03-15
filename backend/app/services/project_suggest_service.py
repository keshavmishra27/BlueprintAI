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
    from .llm_factory import invoke_hybrid_llm
    from langchain_core.messages import SystemMessage, HumanMessage

    system_prompt = """You are a highly creative and strategic career counselor and hackathon mentor. 
    Your goal is to suggest project ideas that either make a resume stand out to top-tier recruiters or win major international hackathons.
    
    For each suggestion, provide:
    - A catchy title
    - A detailed description (2-3 sentences)
    - A modern tech stack
    - A 'USP' (Unique Selling Point) - why it's great for a resume or why it wins a hackathon.
    
    Return ONLY valid JSON with two lists: 'resume_projects' and 'hackathon_projects'."""

    user_prompt = f"""Generate 5 resume-grade projects and 5 hackathon-winning project ideas for the theme(s): {theme}.
    
    Return ONLY this JSON structure:
    {{
        "resume_projects": [
            {{
                "title": "...",
                "description": "...",
                "tech_stack": ["...", "..."],
                "why_great_for_resume": "..."
            }}
        ],
        "hackathon_projects": [
            {{
                "title": "...",
                "description": "...",
                "tech_stack": ["...", "..."],
                "why_it_wins": "..."
            }}
        ]
    }}"""

    response = invoke_hybrid_llm([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ], temperature=0.7)
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
