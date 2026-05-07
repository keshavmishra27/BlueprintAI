from pathlib import Path
"""
project_suggest.py  —  Solara page for the Project Ideas feature.
User enters a theme → AI returns Top 5 Resume + Top 5 Hackathon projects.
"""

import solara
import requests
import os
import threading

from solara_app.components import CountdownTerminal

API = os.getenv("API_URL", "http://localhost:8000")

# ── Persistent Session State ────────────────────────────────────────

SESSION_STATES = {}

def get_session_state():
    sid = solara.get_session_id()
    if sid not in SESSION_STATES:
        SESSION_STATES[sid] = {
            "selected_domains": solara.reactive([]),
            "error_msg": solara.reactive(""),
            "loading": solara.reactive(False),
            "loading_step": solara.reactive(""),
            "result": solara.reactive(None),
            "screen": solara.reactive("form"),
            "initialized": solara.reactive(False),
        }
    return SESSION_STATES[sid]


def _parse_error(r) -> str:
    try:
        return r.json().get("detail", r.text) or r.text
    except Exception:
        return r.text or f"HTTP {r.status_code}"


def _run_suggest(sid: str):
    """Background thread — calls the backend."""
    state = SESSION_STATES.get(sid)
    if not state: return
    
    themes = state["selected_domains"].value
    loading_step = state["loading_step"]
    result = state["result"]
    screen = state["screen"]
    error_msg = state["error_msg"]
    loading = state["loading"]

    try:
        loading_step.set("🧠 AI is brainstorming project ideas…")
        r = requests.post(
            f"{API}/project-suggest/suggest",
            json={"themes": themes},
            timeout=None,
        )
        if r.status_code == 200:
            result.set(r.json())
            screen.set("results")
        else:
            error_msg.set(f"❌ {_parse_error(r)}")
    except Exception as e:
        error_msg.set(f"❌ {e}")
    finally:
        loading.set(False)
        loading_step.set("")


def submit():
    sid = solara.get_session_id()
    state = SESSION_STATES.get(sid)
    if not state: return

    error_msg = state["error_msg"]
    domains = state["selected_domains"].value
    loading = state["loading"]
    loading_step = state["loading_step"]

    error_msg.set("")
    if not domains:
        error_msg.set("Please select at least one theme or domain.")
        return
    
    loading.set(True)
    loading_step.set("🔌 Connecting to backend…")
    threading.Thread(target=_run_suggest, args=(sid,), daemon=True).start()


def reset():
    sid = solara.get_session_id()
    state = SESSION_STATES.get(sid)
    if not state: return
    state["selected_domains"].set([])
    state["error_msg"].set("")
    state["result"].set(None)
    state["loading"].set(False)
    state["screen"].set("form")


# ── Shared Styles ──────────────────────────────────────────────────

CARD_STYLE = (
    "background:rgba(10, 15, 20, 0.7); backdrop-filter:blur(20px);"
    "border:1px solid rgba(0, 255, 204, 0.25); border-radius:16px;"
    "padding:24px; box-shadow:0 8px 32px rgba(0, 0, 0, 0.4);"
    "transition:transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;"
)

CARD_HOVER_CSS = """
.project-card:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 40px rgba(0, 255, 204, 0.25) !important;
    border-color: rgba(0, 255, 204, 0.5) !important;
}
.project-card { transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease; }

.tech-chip {
    display: inline-block;
    background: rgba(0, 136, 255, 0.2);
    border: 1px solid rgba(0, 136, 255, 0.4);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: #7dd3fc;
    margin: 3px 4px 3px 0;
    font-weight: 600;
    letter-spacing: 0.3px;
}

@keyframes fadeInUp {
    from { opacity:0; transform:translateY(20px); }
    to   { opacity:1; transform:translateY(0); }
}
.fade-in-up { animation: fadeInUp 0.5s ease forwards; }

@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 15px rgba(0, 255, 204, 0.3); }
    50%      { box-shadow: 0 0 30px rgba(0, 255, 204, 0.6); }
}
"""


# ── Components ─────────────────────────────────────────────────────

@solara.component
def TechChips(techs: list):
    """Render tech stack as small pill badges."""
    with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:4px; margin-top:10px;"):
        for tech in techs:
            solara.v.Html(
                tag="span",
                class_="tech-chip",
                children=[tech],
            )


@solara.component
def ProjectCard(index: int, title: str, description: str, tech_stack: list, highlight_label: str, highlight_text: str, accent: str):
    """A single glassmorphism project card."""
    with solara.v.Html(
        tag="div",
        class_="project-card fade-in-up",
        style_=(
            f"{CARD_STYLE}"
            f"animation-delay:{index * 0.1}s; opacity:0;"
            f"border-top:3px solid {accent};"
            "margin-bottom:16px;"
        ),
    ):
        # Number badge + title
        with solara.v.Html(tag="div", style_="display:flex; align-items:center; gap:12px; margin-bottom:12px;"):
            solara.v.Html(
                tag="div",
                style_=(
                    f"width:32px; height:32px; border-radius:50%; background:{accent};"
                    "display:flex; align-items:center; justify-content:center;"
                    "font-weight:800; font-size:14px; color:#000; flex-shrink:0;"
                ),
                children=[str(index + 1)],
            )
            solara.Text(
                title,
                style={"font-size": "18px", "font-weight": "700", "color": "#ffffff", "line-height": "1.3"},
            )

        # Description
        solara.Text(
            description,
            style={"font-size": "14px", "color": "rgba(255,255,255,0.8)", "line-height": "1.6", "display": "block", "margin-bottom": "8px"},
        )

        # Tech stack chips
        if tech_stack:
            TechChips(tech_stack)

        # Highlight section (why great for resume / why it wins)
        if highlight_text:
            with solara.v.Html(
                tag="div",
                style_=(
                    f"margin-top:14px; padding:10px 14px; border-radius:10px;"
                    f"background:rgba(0, 255, 204, 0.06); border-left:3px solid {accent};"
                ),
            ):
                solara.Text(
                    highlight_label,
                    style={"font-size": "11px", "text-transform": "uppercase", "letter-spacing": "1px", "color": accent, "font-weight": "700", "display": "block", "margin-bottom": "4px"},
                )
                solara.Text(
                    highlight_text,
                    style={"font-size": "13px", "color": "rgba(255,255,255,0.85)", "line-height": "1.5", "display": "block"},
                )


@solara.component
def FormScreen(selected_domains, error_msg, loading, loading_step, submit_fn):
    with solara.v.Html(tag="div", style_="max-width:680px; margin:40px auto; padding:0 24px;"):
        # Hero section
        solara.Text(
            "🚀 Project Ideas Generator",
            style={
                "font-size": "32px", "font-weight": "800", "color": "#ffffff",
                "margin-bottom": "12px", "display": "block",
                "text-shadow": "0 0 20px rgba(0,255,204,0.4)",
            },
        )
        solara.Text(
            "Enter a theme or domain — the AI agent will suggest the best "
            "industry-grade projects for your resume and innovative ideas "
            "that win hackathons.",
            style={
                "color": "rgba(255,255,255,0.9)", "font-size": "16px",
                "line-height": "1.6", "margin-bottom": "32px", "display": "block",
            },
        )

        # Input card
        with solara.v.Html(tag="div", style_=CARD_STYLE):
            solara.Text(
                "Choose Your Theme",
                style={
                    "font-size": "20px", "font-weight": "700", "color": "#00ffcc",
                    "margin-bottom": "20px", "display": "block",
                    "text-shadow": "0 0 10px rgba(0, 255, 204, 0.3)",
                },
            )

            # Suggested themes
            with solara.v.Html(tag="div", style_="margin-bottom:20px;"):
                solara.Text(
                    "Select one or more themes:",
                    style={"font-size": "13px", "color": "rgba(255,255,255,0.5)", "display": "block", "margin-bottom": "8px"},
                )
                with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:8px;"):
                    for suggestion in ["Artificial Intelligence", "FinTech", "Healthcare", "Web3 / Blockchain", "EdTech", "Sustainability", "Cybersecurity", "IoT", "DSA","ambulance","hospital"]:
                        
                        def toggle_domain(s=suggestion):
                            current = list(selected_domains.value)
                            if s in current: current.remove(s)
                            else: current.append(s)
                            selected_domains.set(current)
                            
                        is_selected = suggestion in selected_domains.value
                        
                        solara.Button(
                            suggestion,
                            on_click=toggle_domain,
                            outlined=not is_selected,
                            color="primary" if is_selected else None,
                            style=(
                                "text-transform:none; font-size:12px; border-radius:20px;"
                                f"border-color:{'transparent' if is_selected else 'rgba(0,136,255,0.4)'}; "
                                f"color:{'#000' if is_selected else '#7dd3fc'};"
                                f"background:{'linear-gradient(90deg, #0088ff, #00ffcc)' if is_selected else 'transparent'};"
                                "padding:2px 14px; min-width:auto;"
                            ),
                        )

            # Display selected domains
            if selected_domains.value:
                with solara.v.Html(tag="div", style_="margin-bottom: 20px; padding: 10px; background: rgba(0, 136, 255, 0.1); border-radius: 8px; border: 1px solid rgba(0, 136, 255, 0.3);"):
                    solara.Text("Selected Domains: ", style={"font-weight": "600", "color": "#7dd3fc", "margin-right": "8px"})
                    for d in selected_domains.value:
                        solara.v.Html(
                            tag="span", 
                            children=[d], 
                            style_="background: rgba(0, 255, 204, 0.2); color: #00ffcc; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-right: 6px; display: inline-block; margin-bottom: 4px; border: 1px solid rgba(0, 255, 204, 0.4);"
                        )

            if error_msg.value:
                with solara.v.Html(
                    tag="div",
                    style_=(
                        "background:rgba(239, 68, 68, 0.2); border:1px solid #ef4444;"
                        "border-radius:8px; padding:12px 16px; margin-top:16px;"
                        "color:#fca5a5; font-size:14px;"
                    ),
                ):
                    solara.Text(f"Error: {error_msg.value}")

            solara.Button(
                "✨ Generate Project Ideas" if not loading.value else "⏳ Thinking… (may take 1–2 min)",
                color="primary",
                on_click=submit_fn,
                disabled=loading.value,
                style=(
                    "width:100%; margin-top:24px; padding:12px; font-weight:700;"
                    "letter-spacing:0.5px; border-radius:8px;"
                    "background:linear-gradient(90deg, #0088ff, #00ffcc);"
                    "border:none; color:#000;"
                ),
            )

        # Loading indicator
        if loading.value:
            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:24px; background:rgba(245, 158, 11, 0.15);"
                    "border-left:4px solid #f59e0b; padding:16px; border-radius:0 8px 8px 0;"
                ),
            ):
                solara.Text(
                    loading_step.value or "⏳ Working…",
                    style={"font-weight": "700", "font-size": "15px", "color": "#fcd34d", "display": "block"},
                )
                solara.Text(
                    "The AI is researching the best projects for your theme. "
                    "This usually takes 1–2 minutes — please keep this tab open!",
                    style={"color": "rgba(255,255,255,0.7)", "font-size": "13px", "margin-top": "6px", "display": "block"},
                )


@solara.component
def ResultsScreen(result, reset_fn):
    r = result.value
    # Defensive check: ensure r is a dictionary. 
    # If it's an int (e.g. status code) or None, show error.
    if not r or not isinstance(r, dict):
        with solara.v.Html(tag="div", style_="max-width:600px; margin:40px auto; padding:24px; text-align:center;"):
            solara.Text("❌ Invalid Result Format", style={"font-size": "24px", "font-weight": "800", "color": "#ef4444", "display": "block", "margin-bottom": "16px"})
            solara.Text(f"Expected a dictionary but received: {type(r).__name__}", style={"color": "rgba(255,255,255,0.7)", "margin-bottom": "24px", "display": "block"})
            solara.Button("Back to Form", on_click=reset_fn, color="primary")
        return

    theme = r.get("theme", r.get("themes", ["Unknown"])[0] if isinstance(r.get("themes"), list) else "Unknown")
    resume_projects = r.get("resume_projects", [])
    hackathon_projects = r.get("hackathon_projects", [])

    with solara.v.Html(tag="div", style_="max-width:900px; margin:40px auto; padding:0 24px;"):
        # Header
        solara.Text(
            f"🚀 Project Ideas for: {theme}",
            style={
                "font-size": "28px", "font-weight": "800", "color": "#ffffff",
                "display": "block", "margin-bottom": "8px",
                "text-shadow": "0 0 20px rgba(0,255,204,0.4)",
            },
        )
        solara.Text(
            f"{len(resume_projects)} resume projects  •  {len(hackathon_projects)} hackathon ideas",
            style={"color": "#00ffcc", "font-size": "14px", "display": "block", "margin-bottom": "32px"},
        )

        # ── Resume Projects Section ──
        with solara.v.Html(tag="div", style_="margin-bottom:40px;"):
            with solara.v.Html(tag="div", style_="display:flex; align-items:center; gap:12px; margin-bottom:20px; padding-bottom:12px; border-bottom:2px solid rgba(0,136,255,0.3);"):
                solara.v.Html(tag="div", style_="width:40px; height:40px; border-radius:12px; background:linear-gradient(135deg, #0088ff, #00bbff); display:flex; align-items:center; justify-content:center; font-size:20px;", children=["🏢"])
                with solara.v.Html(tag="div"):
                    solara.Text("Industry Resume Projects", style={"font-size": "22px", "font-weight": "700", "color": "#ffffff", "display": "block"})
                    solara.Text("Projects that impress recruiters and demonstrate real engineering skills", style={"font-size": "13px", "color": "rgba(255,255,255,0.6)", "display": "block"})

            for i, proj in enumerate(resume_projects):
                ProjectCard(index=i, title=proj.get("title", "Untitled"), description=proj.get("description", ""), tech_stack=proj.get("tech_stack", []), highlight_label="💼 Why Great for Resume", highlight_text=proj.get("why_great_for_resume", ""), accent="#0088ff")

        # ── Hackathon Projects Section ──
        with solara.v.Html(tag="div", style_="margin-bottom:40px;"):
            with solara.v.Html(tag="div", style_="display:flex; align-items:center; gap:12px; margin-bottom:20px; padding-bottom:12px; border-bottom:2px solid rgba(0,255,204,0.3);"):
                solara.v.Html(tag="div", style_="width:40px; height:40px; border-radius:12px; background:linear-gradient(135deg, #00ffcc, #00ff66); display:flex; align-items:center; justify-content:center; font-size:20px;", children=["🏆"])
                with solara.v.Html(tag="div"):
                    solara.Text("Hackathon Winning Projects", style={"font-size": "22px", "font-weight": "700", "color": "#ffffff", "display": "block"})
                    solara.Text("Creative ideas with wow-factor that judges love to pick as winners", style={"font-size": "13px", "color": "rgba(255,255,255,0.6)", "display": "block"})

            for i, proj in enumerate(hackathon_projects):
                ProjectCard(index=i, title=proj.get("title", "Untitled"), description=proj.get("description", ""), tech_stack=proj.get("tech_stack", []), highlight_label="🏆 Why It Wins", highlight_text=proj.get("why_it_wins", ""), accent="#00ffcc")

        # Reset button
        with solara.v.Html(tag="div", style_="margin-top:16px;"):
            solara.Button("🚀 Try Another Theme", color="primary", on_click=reset_fn, style="width:100%; padding:14px; font-weight:700; letter-spacing:0.5px; border-radius:8px; background:linear-gradient(90deg, #0088ff, #00ffcc); border:none; color:#000;")


# ── Main Page ──────────────────────────────────────────────────────

@solara.component
def Page():
    solara.Title("Project Ideas")
    
    # -- Session State --
    state = get_session_state()
    selected_domains = state["selected_domains"]
    error_msg        = state["error_msg"]
    loading          = state["loading"]
    loading_step     = state["loading_step"]
    result           = state["result"]
    screen           = state["screen"]
    initialized      = state["initialized"]

    def on_init():
        if not initialized.value:
            def set_init(): 
                import time
                time.sleep(3.5)
                initialized.set(True)
            threading.Thread(target=set_init, daemon=True).start()
    solara.use_effect(on_init, [])

    if not initialized.value:
        CountdownTerminal()

    solara.HTML(tag="style", unsafe_innerHTML=f"""
        .v-application, .v-application--wrap, .v-main, .v-main__wrap, .v-sheet {{ background-color: #030812 !important; background: #030812 !important; }}
        .theme--light.v-sheet {{ background-color: #030812 !important; }}
        body {{ background-color: #030812 !important; background: #030812 !important; margin: 0; min-height: 100vh; }}
        .v-text-field input, .v-textarea textarea, .v-input input {{ color: #00f0ff !important; text-shadow: 0 0 8px rgba(0, 240, 255, 0.4); font-weight: 600; }}
        .v-text-field .v-label {{ color: rgba(255,255,255,0.6) !important; }}
        {CARD_HOVER_CSS}
    """)

    with solara.v.Html(tag="div", style_="min-height:100vh; background: #030812; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; color:#ffffff; padding-bottom:60px; box-sizing:border-box;"):
        if screen.value == "form":
            FormScreen(selected_domains, error_msg, loading, loading_step, submit)
        else:
            ResultsScreen(result, reset)
