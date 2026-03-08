import solara
import requests
import os
import threading

from solara_app.components import CountdownTerminal

API = os.getenv("API_URL", "http://localhost:8000")

github_url    = solara.reactive("")
student_name  = solara.reactive("")
error_msg     = solara.reactive("")
loading       = solara.reactive(False)
loading_step  = solara.reactive("")   
result        = solara.reactive(None) 
screen        = solara.reactive("form") 


def _parse_error(r) -> str:
    try:
        return r.json().get("detail", r.text) or r.text
    except Exception:
        return r.text or f"HTTP {r.status_code}"


def _run_analysis(url: str, name: str):
    """Runs in a background thread — never blocks Solara's render thread."""
    try:
        loading_step.set("📡 Scraping GitHub repository files…")
        r = requests.post(
            f"{API}/repo-judge/analyze",
            json={"github_url": url, "student_name": name},
            timeout=None,   
        )
        loading_step.set("🧠 LLM is reading the code and writing verdict…")
        if r.status_code == 200:
            result.set(r.json())
            screen.set("results")
        else:
            error_msg.set(f" {_parse_error(r)}")
    except Exception as e:
        error_msg.set(f" {e}")
    finally:
        loading.set(False)
        loading_step.set("")


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
    t = threading.Thread(target=_run_analysis, args=(url, name), daemon=True)
    t.start()


def reset():
    github_url.set("")
    student_name.set("")
    error_msg.set("")
    result.set(None)
    loading.set(False)
    screen.set("form")


SCORE_META = {
    "code_quality_score":   ("Code Quality",   "#00ffcc"),
    "innovation_score":     ("Innovation",     "#0088ff"),
    "completeness_score":   ("Completeness",   "#00ff66"),
    "documentation_score":  ("Documentation",  "#00bbff"),
}


@solara.component
def ScoreBar(label: str, value: int, color: str, max_val: int = 25):
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
                children=[],
            )


@solara.component
def BulletList(items: list, icon: str, color: str):
    for item in items:
        with solara.v.Html(tag="div", style_="display:flex; align-items:flex-start; gap:8px; margin-bottom:8px;"):
            solara.Text(icon, style={"color": color, "font-size": "15px", "flex-shrink": "0", "margin-top": "2px"})
            solara.Text(item, style={"font-size": "14px", "line-height": "1.6", "color": "#f8fafc"})


@solara.component
def FormScreen():
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
                style="width:100%; margin-bottom:16px;",
            )
            solara.InputText(
                "GitHub Repository URL  (e.g. https://github.com/owner/repo)",
                value=github_url,
                style="width:100%;",
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
                on_click=analyze,
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
def ResultsScreen():
    r = result.value
    if not r:
        return

    total = r.get("overall_score", 0)
    color = "#00ffcc" if total >= 75 else "#f59e0b" if total >= 50 else "#ef4444"
    grade = (
        "Hackathon Ready 🚀" if total >= 80 else
        "Strong Contender 💪" if total >= 60 else
        "Needs More Work 📚"
    )

    with solara.v.Html(tag="div", style_="max-width:760px; margin:40px auto; padding:0 24px;"):
        solara.Text(f"🧑‍⚖️ Judge Verdict: {r.get('student_name', '')}", style={"font-size": "28px", "font-weight": "800", "color": "#ffffff", "display": "block", "margin-bottom":"8px", "text-shadow": "0 0 20px rgba(0,255,204,0.4)"})
        solara.Text(
            r.get("repository", ""),
            style={"color": "#00ffcc", "font-size": "14px", "display": "block", "margin-bottom": "24px"}
        )

        with solara.v.Html(
            tag="div",
            style_=(
                f"text-align:center; padding:32px; border-top:4px solid {color};"
                "background:rgba(10, 15, 20, 0.7); backdrop-filter:blur(20px);"
                "border-radius:16px; box-shadow:0 8px 32px rgba(0, 0, 0, 0.4);"
            )
        ):
            solara.Text("Overall Score", style={"color": "rgba(255,255,255,0.6)", "font-size": "14px", "text-transform": "uppercase", "letter-spacing": "1px", "display": "block"})
            solara.Text(
                f"{total}/100",
                style={"font-size": "64px", "font-weight": "900", "color": color, "display": "block", "line-height": "1.1", "margin": "8px 0"}
            )
            solara.Text(grade, style={"color": color, "font-size": "18px", "font-weight": "700", "display": "block"})
            verdict = r.get("verdict", "")
            if verdict:
                solara.Text(
                    f'"{verdict}"',
                    style={"color": "rgba(255,255,255,0.8)", "font-size": "15px", "margin-top": "16px", "font-style": "italic", "display": "block", "line-height": "1.6"}
                )

        with solara.v.Html(
            tag="div",
            style_=(
                "margin-top:24px; padding:24px; border-radius:16px;"
                "background:rgba(10, 15, 20, 0.7); backdrop-filter:blur(20px);"
                "border:1px solid rgba(0, 255, 204, 0.2);"
            )
        ):
            solara.Text("📊 Score Breakdown", style={"font-size": "18px", "font-weight": "700", "color": "#0088ff", "display": "block", "margin-bottom": "20px"})
            for key, (label, bar_color) in SCORE_META.items():
                ScoreBar(label, r.get(key, 0), bar_color)

        readiness = r.get("hackathon_readiness", "")
        if readiness:
            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:24px; padding:24px; border-radius:16px;"
                    "background:rgba(10, 15, 20, 0.7); backdrop-filter:blur(20px);"
                    "border:1px solid rgba(0, 255, 204, 0.2);"
                )
            ):
                solara.Text("🎯 Hackathon Readiness", style={"font-size": "18px", "font-weight": "700", "color": "#0088ff", "display": "block", "margin-bottom": "16px"})
                solara.Text(readiness, style={"font-size": "15px", "line-height": "1.7", "color": "#f8fafc", "display": "block"})

        strengths    = r.get("strengths", [])
        improvements = r.get("improvements", [])
        if strengths or improvements:
            with solara.v.Html(tag="div", style_="display:flex; gap:24px; margin-top:24px; flex-wrap:wrap;"):
                if strengths:
                    with solara.v.Html(
                        tag="div",
                        style_=(
                            "flex:1; min-width:300px; padding:24px; border-radius:16px;"
                            "background:rgba(16, 185, 129, 0.1); border:1px solid rgba(16, 185, 129, 0.3);"
                        )
                    ):
                        solara.Text("✅ What's Good", style={"font-size": "18px", "font-weight": "700", "color": "#10b981", "display": "block", "margin-bottom": "16px"})
                        BulletList(strengths, icon="✓", color="#10b981")
                if improvements:
                    with solara.v.Html(
                        tag="div",
                        style_=(
                            "flex:1; min-width:300px; padding:24px; border-radius:16px;"
                            "background:rgba(245, 158, 11, 0.1); border:1px solid rgba(245, 158, 11, 0.3);"
                        )
                    ):
                        solara.Text("⚠️ Improvements Needed", style={"font-size": "18px", "font-weight": "700", "color": "#f59e0b", "display": "block", "margin-bottom": "16px"})
                        BulletList(improvements, icon="!", color="#f59e0b")

        standout  = r.get("standout_files", [])
        problem   = r.get("problem_areas", [])
        if standout or problem:
            with solara.v.Html(tag="div", style_="display:flex; gap:24px; margin-top:24px; flex-wrap:wrap;"):
                if standout:
                    with solara.v.Html(
                        tag="div",
                        style_=(
                            "flex:1; min-width:300px; padding:24px; border-radius:16px;"
                            "background:rgba(0, 255, 204, 0.1); border:1px solid rgba(0, 255, 204, 0.3);"
                        )
                    ):
                        solara.Text("🌟 Standout Files", style={"font-size": "18px", "font-weight": "700", "color": "#00ffcc", "display": "block", "margin-bottom": "16px"})
                        BulletList(standout, icon="*", color="#00ffcc")
                if problem:
                    with solara.v.Html(
                        tag="div",
                        style_=(
                            "flex:1; min-width:300px; padding:24px; border-radius:16px;"
                            "background:rgba(239, 68, 68, 0.1); border:1px solid rgba(239, 68, 68, 0.3);"
                        )
                    ):
                        solara.Text("🚨 Problem Areas", style={"font-size": "18px", "font-weight": "700", "color": "#ef4444", "display": "block", "margin-bottom": "16px"})
                        BulletList(problem, icon="×", color="#ef4444")

        with solara.v.Html(tag="div", style_="margin-top:32px;"):
            solara.Button(
                "🧑‍⚖️ Judge Another Repo",
                color="primary",
                on_click=reset,
                style="width:100%; padding:14px; font-weight:700; letter-spacing:0.5px; border-radius:8px; background:linear-gradient(90deg, #0088ff, #00ffcc); border:none; color:#000;",
            )


@solara.component
def Page():
    solara.Title("Repo Judge")
    CountdownTerminal()

    # Global CSS injection for animations and global resets
    solara.HTML(tag="style", unsafe_innerHTML="""
        .v-application, .v-application--wrap, .v-main__wrap {
            background: transparent !important;
        }
        body {
            background-color: #030812 !important;
            margin: 0;
            min-height: 100vh;
        }

        /* Astonishing Neon Input Fields */
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

        /* Electric Neon Typing Text */
        .v-text-field input, .v-textarea textarea, .v-input input {
            color: #00f0ff !important;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.8);
            font-weight: 700 !important;
            letter-spacing: 1px;
        }
        
        /* Vibrant Floating Labels */
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

        /* Fixes for any other random Vuetify elements */
        .v-card, .v-sheet, .v-messages__message {
            background-color: transparent !important;
            color: #00f0ff !important;
        }
    """)

    # We wrap the entire page in a pure HTML div with the animated gradient to bypass Vuetify completely
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
            FormScreen()
        else:
            ResultsScreen()
