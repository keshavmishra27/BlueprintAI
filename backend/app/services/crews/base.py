import logging
import os

from crewai import Agent, Crew, Process, Task

from backend.app.services.llm_factory import extract_json_from_text, get_hybrid_crew_llm

logger = logging.getLogger(__name__)
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")


def _crew_result_text(result) -> str:
    if result is None:
        return ""
    if hasattr(result, "raw"):
        return str(result.raw)
    return str(result)


def run_crew(agents: list, tasks: list, inputs: dict | None = None) -> str:
    llm = get_hybrid_crew_llm()
    for agent in agents:
        agent.llm = llm
    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff(inputs=inputs or {})
    return _crew_result_text(result)


def parse_json_output(raw: str) -> dict:
    data = extract_json_from_text(raw)
    return data if isinstance(data, dict) else {}


def parse_json_list_output(raw: str) -> list:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    import json

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    data = extract_json_from_text(text)
    if isinstance(data, list):
        return data
    return []
