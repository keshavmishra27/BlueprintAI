import os
import threading

import solara

from solara_app.api_client import api_post
from solara_app.components import CountdownTerminal

SESSION_STATES = {}


def get_session_state():
    sid = solara.get_session_id()
    if sid not in SESSION_STATES:
        SESSION_STATES[sid] = {
            "subject_name": solara.reactive(""),
            "subject_type": solara.reactive("project"),
            "description": solara.reactive(""),
            "loading": solara.reactive(False),
            "error_msg": solara.reactive(""),
            "result": solara.reactive(None),
            "screen": solara.reactive("form"),
            "initialized": solara.reactive(False),
        }
    return SESSION_STATES[sid]


def _run_swot(sid: str):
    state = SESSION_STATES.get(sid)
    if not state:
        return
    try:
        r = api_post(
            "/swot/analyze",
            {
                "subject_name": state["subject_name"].value,
                "subject_type": state["subject_type"].value,
                "description": state["description"].value,
            },
            timeout=180,
        )
        if r.status_code == 200:
            state["result"].set(r.json())
            state["screen"].set("results")
        else:
            state["error_msg"].set(r.text)
    except Exception as e:
        state["error_msg"].set(str(e))
    finally:
        state["loading"].set(False)


@solara.component
def Quadrant(title: str, items: list, color: str):
    solara.Text(title, style={"font-weight": "800", "font-size": "18px", "color": color, "margin-bottom": "12px"})
    for item in items or []:
        if isinstance(item, dict):
            solara.Text(f"• {item.get('title', item.get('detail', ''))}", style={"font-size": "14px", "margin-bottom": "6px"})
            if item.get("detail"):
                solara.Text(item["detail"], style={"font-size": "13px", "color": "#64748b", "margin-bottom": "10px"})
        else:
            solara.Text(f"• {item}", style={"font-size": "14px", "margin-bottom": "6px"})


@solara.component
def Page():
    solara.Title("SWOT Analysis")
    state = get_session_state()

    def run_analysis():
        if not state["subject_name"].value.strip() or not state["description"].value.strip():
            state["error_msg"].set("Name and description are required.")
            return
        state["loading"].set(True)
        state["error_msg"].set("")
        threading.Thread(target=_run_swot, args=(solara.get_session_id(),), daemon=True).start()

    if not state["initialized"].value:
        CountdownTerminal()
        solara.use_effect(lambda: threading.Timer(3.5, lambda: state["initialized"].set(True)).start(), [])

    with solara.Column(style={"max-width": "800px", "margin": "0 auto", "padding": "24px"}):
        solara.Markdown("## SWOT Analysis (CrewAI)")
        solara.InputText("Subject name", value=state["subject_name"])
        with solara.Row():
            solara.Button("Project", on_click=lambda: state["subject_type"].set("project"))
            solara.Button("Idea", on_click=lambda: state["subject_type"].set("idea"))
        solara.Text(f"Type: {state['subject_type'].value}")
        solara.InputTextArea("Description", value=state["description"], continuous_update=True)
        solara.Button("Run SWOT", on_click=run_analysis, disabled=state["loading"].value)
        if state["error_msg"].value:
            solara.Error(state["error_msg"].value)
        if state["screen"].value == "results" and state["result"].value:
            r = state["result"].value
            with solara.Columns([1, 1]):
                with solara.Column():
                    Quadrant("Strengths", r.get("strengths", []), "#059669")
                    Quadrant("Weaknesses", r.get("weaknesses", []), "#dc2626")
                with solara.Column():
                    Quadrant("Opportunities", r.get("opportunities", []), "#2563eb")
                    Quadrant("Threats", r.get("threats", []), "#d97706")
            if r.get("strategic_recommendations"):
                solara.Markdown("### Recommendations")
                for rec in r["strategic_recommendations"]:
                    solara.Text(str(rec))
