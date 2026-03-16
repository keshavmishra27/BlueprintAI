from pathlib import Path
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
            "github_url": solara.reactive(""),
            "student_name": solara.reactive(""),
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


def _run_analysis(sid: str):
    """Runs in a background thread."""
    state = SESSION_STATES.get(sid)
    if not state: return
    
    url = state["github_url"].value
    name = state["student_name"].value
    loading = state["loading"]
    loading_step = state["loading_step"]
    result = state["result"]
    screen = state["screen"]
    error_msg = state["error_msg"]

    try:
        loading_step.set("⚡ Fast-Scraping repository archive...")
        r = requests.post(
            f"{API}/repo-judge/analyze",
            json={"github_url": url, "student_name": name},
            timeout=None,   
        )
        loading_step.set("🧠 AI is deep-reading the code (takes 1-3 mins)...")
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


@solara.component
def ScoreBar(label: str, value: float, color: str, max_val: int = 10):
    pct = int(min(100.0, float((value / max_val) * 100)))
    with solara.v.Html(tag="div", style_="margin-bottom:14px;"):
        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;"):
            solara.Text(label, style={"font-weight": "600", "font-size": "14px", "color": "#ffffff"})
            solara.Text(
                f"{value}/{max_val}",
                style={"color": color, "font-weight": "700", "font-size": "14px"},
            )
        with solara.v.Html(tag="div", style_="background:rgba(255,255,255,0.2); border-radius:9999px; height:10px; width:100%; overflow:hidden;"):
            solara.v.Html(
                tag="div",
                style_=(
                    f"background:{color}; border-radius:9999px; height:10px;"
                    f"width:{pct}%; transition:width 0.8s ease;"
                    "box-shadow:0 0 10px rgba(0, 255, 204, 0.5);"
                ),
            )

@solara.component
def BulletList(items: list, icon: str, color: str):
    for item in items:
        with solara.v.Html(tag="div", style_="display:flex; align-items:flex-start; gap:8px; margin-bottom:8px;"):
            solara.Text(icon, style={"color": color, "font-size": "15px", "flex-shrink": "0", "margin-top": "2px"})
            solara.Text(item, style={"font-size": "14px", "line-height": "1.6", "color": "#f8fafc"})


solara.Style(Path(__file__).parent.parent / 'assets' / 'custom.css')

@solara.component
def SecuritySection(warnings: list):
    if not warnings: return
    with solara.v.Html(tag="div", style_="margin-top:24px; padding:20px; border-radius:12px; background:rgba(239, 68, 68, 0.1); border:1px solid rgba(239, 68, 68, 0.3);"):
        solara.Text("🛡️ Security Warnings", style={"font-size": "18px", "font-weight": "700", "color": "#f87171", "display": "block", "margin-bottom": "16px"})
        for w in warnings:
            with solara.v.Html(tag="div", style_="margin-bottom:16px; border-bottom:1px solid rgba(239,68,68,0.1); padding-bottom:12px;"):
                solara.Text(f"Type: {w.get('type','leak').upper()}", style={"color":"#ef4444", "font-weight":"800", "font-size":"12px", "display":"block"})
                solara.Text(f"Evidence: {w.get('evidence','')}", style={"color":"#fca5a5", "font-size":"13px", "display":"block", "margin-top":"4px", "font-family":"monospace"})
                solara.Text(f"Fix: {w.get('remediation','')}", style={"color":"#10b981", "font-size":"13px", "display":"block", "margin-top":"4px"})

@solara.component
def IssuesSection(issues: list):
    if not issues: return
    with solara.v.Html(tag="div", style_="margin-top:24px;"):
        solara.Text("⚠️ Top Issues & Fixes", style={"font-size": "20px", "font-weight": "800", "color": "#f59e0b", "display": "block", "margin-bottom": "20px"})
        for iss in issues:
            sev = iss.get("severity", "major").lower()
            scolor = "#ef4444" if sev == "critical" else "#f59e0b" if sev == "major" else "#0ea5e9"
            with solara.v.Html(tag="div", style_=f"margin-bottom:20px; padding:20px; border-radius:16px; background:rgba(15,23,42,0.6); border-left:6px solid {scolor};"):
                with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:flex-start;"):
                    solara.Text(iss.get("title",""), style={"font-weight":"800", "color":"#ffffff", "font-size":"16px"})
                    solara.Text(sev.upper(), style={"font-size":"10px", "background":scolor, "color":"#000", "padding":"2px 8px", "border-radius":"4px", "font-weight":"999"})
                
                solara.Text(iss.get("description",""), style={"font-size":"14px", "color":"#cbd5e1", "display":"block", "margin-top":"8px", "line-height":"1.6"})
                
                if iss.get("files"):
                    for fp in iss["files"]:
                        with solara.v.Html(tag="div", style_="margin-top:12px; padding:10px; background:rgba(0,0,0,0.4); border-radius:8px; border:1px solid rgba(255,255,255,0.05);"):
                            solara.Text(f"📄 {fp.get('path')} (Lines {fp.get('lines')})", style={"font-size":"12px", "color":"#94a3b8", "font-family":"monospace"})
                            if fp.get("excerpt"):
                                solara.v.Html(tag="pre", children=[solara.Text(fp.get("excerpt"))], style_="font-size:11px; color:#6366f1; margin-top:4px;")

                solara.Text(f"⏱️ Estimated Effort: {iss.get('estimated_effort_hours', 0)}h", style={"font-size":"12px", "color":scolor, "margin-top":"12px", "display":"block", "font-weight":"600"})


@solara.component
def FormScreen(github_url, student_name, error_msg, loading, loading_step, analyze_fn):
    with solara.v.Html(tag="div", style_="max-width:680px; margin:40px auto; padding:0 24px;"):
        solara.Text("🧑‍⚖️ GitHub Repo Judge", style={"font-size": "32px", "font-weight": "800", "color": "#ffffff", "margin-bottom": "12px", "display": "block", "text-shadow": "0 0 20px rgba(0,255,204,0.4)"})
        solara.Text(
            "Paste your student's public GitHub repository URL. "
            "The AI will read the entire codebase and return a hackathon judge verdict "
            "— scores, strengths, and concrete improvements.",
            style={"color": "rgba(255,255,255,0.9)", "font-size": "16px", "line-height": "1.6", "margin-bottom": "32px", "display": "block"}
        )

        with solara.v.Html(
            tag="div",
            style_=(
                "background:rgba(10, 15, 20, 0.7); backdrop-filter:blur(20px);"
                "border:1px solid rgba(0, 255, 204, 0.3); border-radius:16px;"
                "padding:32px; box-shadow:0 8px 32px rgba(0, 0, 0, 0.4);"
            )
        ):
            solara.Text("Judge a Repository", style={"font-size": "20px", "font-weight": "700", "color": "#00ffcc", "margin-bottom": "24px", "display": "block", "text-shadow": "0 0 10px rgba(0,255,204,0.3)"})
            solara.InputText(
                "Student Name",
                value=student_name,
                classes=["full-width", "mb-4"],
            )
            solara.InputText(
                "GitHub Repository URL  (e.g. https://github.com/owner/repo)",
                value=github_url,
                classes=["full-width"],
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
                "🔍 Analyze Repository" if not loading.value else "⏳ Analyzing… (may take 1–3 min)",
                color="primary",
                on_click=analyze_fn,
                disabled=loading.value,
                style="width:100%; margin-top:24px; padding:12px; font-weight:700; letter-spacing:0.5px; border-radius:8px; background:linear-gradient(90deg, #0088ff, #00ffcc); border:none; color:#000;",
            )

        if loading.value:
            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:24px; background:rgba(245, 158, 11, 0.15);"
                    "border-left:4px solid #f59e0b; padding:16px; border-radius:0 8px 8px 0;"
                )
            ):
                solara.Text(
                    loading_step.value or "⏳ Working…",
                    style={"font-weight": "700", "font-size": "15px", "color": "#fcd34d", "display": "block"}
                )
                solara.Text(
                    "Ollama reads the whole codebase then writes a verdict. "
                    "This can take 2–5 minutes for large repos — please keep this tab open!",
                    style={"color": "rgba(255,255,255,0.7)", "font-size": "13px", "margin-top": "6px", "display": "block"}
                )



@solara.component
def ResultsScreen(result, reset_fn):
    r = result.value
    if not r: return

    total = r.get("total_score", r.get("overall_score", 0))
    color = "#00ffcc" if total >= 75 else "#f59e0b" if total >= 50 else "#ef4444"
    grade = (
        "Expert Recommended 🏆" if total >= 85 else
        "High Quality 🚀" if total >= 70 else
        "Standard Prototype 💪" if total >= 50 else
        "Needs Significant Work 📚"
    )

    with solara.v.Html(tag="div", style_="max-width:860px; margin:40px auto; padding:24px; padding-bottom:100px;"):
        # Header
        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:32px;"):
            with solara.v.Html(tag="div"):
                solara.Text(f"🧑‍⚖️ Expert Verdict: {r.get('student_name', 'Student')}", style={"font-size": "32px", "font-weight": "800", "color": "#ffffff", "display": "block"})
                solara.Text(r.get("repo_url", r.get("repository","")), style={"color": "#6366f1", "font-size": "14px", "display": "block", "margin-top": "4px"})
            
            with solara.v.Html(tag="div", style_=f"text-align:right; border-right:4px solid {color}; padding-right:20px;"):
                solara.Text("TOTAL SCORE", style={"color": "rgba(255,255,255,0.4)", "font-size": "11px", "letter-spacing": "2px"})
                solara.Text(f"{int(total)}/100", style={"font-size": "48px", "font-weight": "900", "color": color, "display": "block", "line-height": "1"})
        
        # Accessibility & Languages (Badges)
        with solara.v.Html(tag="div", style_="display:flex; gap:12px; margin-bottom:32px; flex-wrap:wrap;"):
            solara.v.Html(tag="div", children=[solara.Text(f"🔓 {r.get('accessibility','public').upper()}")], style_=f"padding:4px 12px; border-radius:100px; background:rgba(0,255,204,0.1); border:1px solid rgba(0,255,204,0.3); color:#00ffcc; font-size:12px; font-weight:700;")
            for lang in r.get("languages", []):
                solara.v.Html(tag="div", children=[solara.Text(lang.upper())], style_="padding:4px 12px; border-radius:100px; background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.3); color:#818cf8; font-size:12px; font-weight:700;")

        # Metrics & Reasons
        with solara.v.Html(tag="div", style_="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:24px; margin-bottom:40px;"):
            scores_data = r.get("scores", {})
            metrics = [
                ("Functionality", "functionality", "#00ffcc"),
                ("Code Quality", "code_quality", "#0088ff"),
                ("Documentation", "documentation", "#00ff66"),
                ("Architecture", "architecture", "#f59e0b"),
                ("Testing & CI", "testing_ci", "#6366f1"),
                ("Innovation & UX", "innovation_ux", "#ff007f"),
            ]
            for label, key, mcolor in metrics:
                sd = scores_data.get(key, {})
                with solara.v.Html(tag="div", style_="background:rgba(15,23,42,0.4); border:1px solid rgba(255,255,255,0.05); padding:20px; border-radius:16px;"):
                    ScoreBar(label, sd.get("score", 0), mcolor, max_val=10)
                    if sd.get("reasons"):
                        BulletList(sd["reasons"][:2], icon="•", color="rgba(255,255,255,0.4)")

        # Mentor Notes
        if r.get("mentor_notes"):
             with solara.v.Html(tag="div", style_="margin-bottom:40px; padding:24px; border-radius:16px; background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.2);"):
                solara.Text("🎙️ Mentor Verdict", style={"font-size": "20px", "font-weight": "800", "color": "#818cf8", "display": "block", "margin-bottom": "12px"})
                solara.Text(r["mentor_notes"], style={"font-size": "15px", "line-height": "1.7", "color": "#e2e8f0", "font-style": "italic"})

        # Strengths & Security
        with solara.v.Html(tag="div", style_="display:grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap:24px;"):
            if r.get("strengths"):
                with solara.v.Html(tag="div", style_="padding:24px; border-radius:16px; background:rgba(16,185,129,0.05); border:1px solid rgba(16,185,129,0.2);"):
                    solara.Text("🚀 Key Strengths", style={"font-size": "20px", "font-weight": "800", "color": "#10b981", "display": "block", "margin-bottom": "16px"})
                    BulletList(r["strengths"], icon="✓", color="#10b981")
            SecuritySection(r.get("security_warnings", []))

        # Reproduction & Issues
        IssuesSection(r.get("top_issues", []))

        # Suggested GitHub Issues
        if r.get("suggested_github_issues"):
            with solara.v.Html(tag="div", style_="margin-top:40px;"):
                solara.Text("📌 Suggested GitHub Issues", style={"font-size": "20px", "font-weight": "800", "color": "#0ea5e9", "display": "block", "margin-bottom": "20px"})
                for git_iss in r["suggested_github_issues"]:
                    with solara.v.Html(tag="div", style_="margin-bottom:16px; padding:16px; border-radius:12px; background:rgba(14,165,233,0.05); border:1px solid rgba(14,165,233,0.2);"):
                        solara.Text(f"Issue: {git_iss.get('title')}", style={"font-weight":"700", "color":"#38bdf8", "font-size":"14px"})
                        solara.Text(git_iss.get("body","")[:150] + "...", style={"font-size":"12px", "color":"#94a3b8", "display":"block", "margin-top":"4px"})

        # Reset button
        with solara.v.Html(tag="div", style_="margin-top:48px; border-top:1px solid rgba(255,255,255,0.1); padding-top:32px;"):
            solara.Button("🧑‍⚖️ Judge Another Project", color="primary", on_click=reset_fn, style="width:100%; padding:14px; font-weight:800; border-radius:8px; background:linear-gradient(90deg, #6366f1, #00ffcc); color:#000;")


@solara.component
def Page():
    solara.Title("Repo Judge")
    
    # ── Session States ──────────────────────────────────────────────
    state = get_session_state()
    github_url    = state["github_url"]
    student_name  = state["student_name"]
    error_msg     = state["error_msg"]
    loading       = state["loading"]
    loading_step  = state["loading_step"]   
    result        = state["result"] 
    screen        = state["screen"] 
    initialized   = state["initialized"]

    def analyze():
        error_msg.set("")
        url  = github_url.value.strip()
        name = student_name.value.strip()

        if not url:
            error_msg.set("Please enter a GitHub repository URL.")
            return
        if "github.com" not in url:
            error_msg.set("URL must be a valid github.com link.")
            return
        if not name:
            error_msg.set("Please enter the student's name.")
            return

        loading.set(True)
        loading_step.set("🔌 Connecting to backend…")
        sid = solara.get_session_id()
        t = threading.Thread(
            target=_run_analysis, 
            args=(sid,), 
            daemon=True
        )
        t.start()

    def reset():
        github_url.set("")
        student_name.set("")
        error_msg.set("")
        result.set(None)
        loading.set(False)
        screen.set("form")

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

    solara.HTML(tag="style", unsafe_innerHTML="""
        .v-application, .v-application--wrap, .v-main, .v-main__wrap, .v-sheet {
            background-color: #030812 !important;
            background: #030812 !important;
        }
        .theme--light.v-sheet {{ background-color: #030812 !important; }}
        body {
            background-color: #030812 !important;
            background: #030812 !important;
            margin: 0;
            min-height: 100vh;
        }

        .v-text-field > .v-input__control > .v-input__slot {
            background: rgba(10, 5, 30, 0.8) !important;
            border: 1px solid rgba(255, 0, 128, 0.5) !important;
            border-radius: 12px !important;
            box-shadow: inset 0 0 15px rgba(255, 0, 128, 0.1), 0 0 10px rgba(0, 240, 255, 0.1) !important;
            transition: all 0.4s ease;
        }
        .v-text-field > .v-input__control > .v-input__slot:hover {
            background: rgba(15, 10, 40, 0.9) !important;
            border-color: #00f0ff !important;
            box-shadow: inset 0 0 20px rgba(0, 240, 255, 0.2), 0 0 15px rgba(0, 240, 255, 0.4) !important;
        }
        .v-input--is-focused > .v-input__control > .v-input__slot {
            background: rgba(20, 10, 50, 0.9) !important;
            border-color: #00f0ff !important;
            box-shadow: inset 0 0 25px rgba(0, 240, 255, 0.3), 0 0 20px rgba(0, 240, 255, 0.6) !important;
        }
        .v-text-field > .v-input__control > .v-input__slot::before,
        .v-text-field > .v-input__control > .v-input__slot::after {
            display: none !important;
        }

        .v-text-field input, .v-textarea textarea, .v-input input {
            color: #00f0ff !important;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.8);
            font-weight: 700 !important;
            letter-spacing: 1px;
        }
        
        .v-text-field .v-label {
            color: #ff007f !important;
            font-weight: 700;
            text-shadow: 0 0 5px rgba(255, 0, 127, 0.4);
            letter-spacing: 0.5px;
        }
        .v-text-field .v-label--active {
            color: #00f0ff !important;
            text-shadow: 0 0 8px rgba(0, 240, 255, 0.6);
            transform: translateY(-20px) scale(0.85);
        }

        .v-card, .v-sheet, .v-messages__message {
            background-color: transparent !important;
            color: #00f0ff !important;
        }
    """)

    with solara.v.Html(
        tag="div",
        style_=(
            "min-height:100vh;"
            "background: #030812;"
            "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
            "color:#ffffff;"
            "padding-bottom:60px;"
            "box-sizing:border-box;"
        )
    ):
        if screen.value == "form":
            FormScreen(github_url, student_name, error_msg, loading, loading_step, analyze)
        else:
            ResultsScreen(result, reset)
