import solara
import requests
import os
import threading

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
    "code_quality_score":   ("Code Quality",   "#6366f1"),
    "innovation_score":     ("Innovation",     "#f59e0b"),
    "completeness_score":   ("Completeness",   "#10b981"),
    "documentation_score":  ("Documentation",  "#3b82f6"),
}


@solara.component
def ScoreBar(label: str, value: int, color: str, max_val: int = 25):
    pct = min(100, (value / max_val) * 100)
    with solara.Column(style="margin-bottom:14px;"):
        with solara.Row(justify="space-between"):
            solara.Text(label, style="font-weight:600; font-size:14px;")
            solara.Text(
                f"{value}/{max_val}",
                style=f"color:{color}; font-weight:700;",
            )
        with solara.Div(style="background:#e5e7eb; border-radius:9999px; height:10px; width:100%;"):
            with solara.Div(
                style=(
                    f"background:{color}; border-radius:9999px; height:10px;"
                    f"width:{pct}%; transition:width 0.8s ease;"
                )
            ):
                pass


@solara.component
def BulletList(items: list, icon: str, color: str):
    for item in items:
        with solara.Row(style="align-items:flex-start; gap:6px; margin-bottom:6px;"):
            solara.Text(icon, style=f"color:{color}; font-size:14px; flex-shrink:0;")
            solara.Text(item, style="font-size:13px; line-height:1.6;")


@solara.component
def FormScreen():
    with solara.Column(style="max-width:640px; margin:0 auto; padding:32px;"):
        solara.Markdown("# 🧑‍⚖️ GitHub Repo Judge")
        solara.Markdown(
            "Paste your student's **public** GitHub repository URL. "
            "The AI will read the entire codebase and return a **hackathon judge verdict** "
            "— scores, strengths, and concrete improvements."
        )

        with solara.Card("Judge a Repository"):
            solara.InputText(
                "Student Name",
                value=student_name,
                style="width:100%; margin-bottom:12px;",
            )
            solara.InputText(
                "GitHub Repository URL  (e.g. https://github.com/owner/repo)",
                value=github_url,
                style="width:100%;",
            )

        if error_msg.value:
            solara.Text(error_msg.value, style="color:#ef4444; margin-top:8px;")

        solara.Button(
            "🔍 Analyze Repository" if not loading.value else "⏳ Analyzing… (may take 1–3 min)",
            color="primary",
            on_click=analyze,
            disabled=loading.value,
            style="width:100%; margin-top:16px;",
        )

        if loading.value:
            with solara.Card(style="margin-top:16px; background:#fffbeb; border-left:4px solid #f59e0b;"):
                solara.Text(
                    loading_step.value or "⏳ Working…",
                    style="font-weight:600; font-size:14px;",
                )
                solara.Text(
                    "Ollama reads the whole codebase then writes a verdict. "
                    "This can take 2–5 minutes for large repos — please keep this tab open!",
                    style="color:#78716c; font-size:13px; margin-top:4px;",
                )


@solara.component
def ResultsScreen():
    r = result.value
    if not r:
        return

    total = r.get("overall_score", 0)
    color = "#10b981" if total >= 75 else "#f59e0b" if total >= 50 else "#ef4444"
    grade = (
        "Hackathon Ready 🚀" if total >= 80 else
        "Strong Contender 💪" if total >= 60 else
        "Needs More Work 📚"
    )

    with solara.Column(style="max-width:720px; margin:0 auto; padding:32px;"):
        solara.Markdown(f"# 🧑‍⚖️ Judge Verdict: {r.get('student_name', '')}")
        solara.Text(
            r.get("repository", ""),
            style="color:#6366f1; font-size:13px; margin-bottom:16px;",
        )

        with solara.Card(style=f"text-align:center; padding:28px; border-top:4px solid {color};"):
            solara.Text("Overall Score", style="color:#888; font-size:14px;")
            solara.Text(
                f"{total}/100",
                style=f"font-size:56px; font-weight:900; color:{color};",
            )
            solara.Text(grade, style=f"color:{color}; font-size:17px; font-weight:600;")
            verdict = r.get("verdict", "")
            if verdict:
                solara.Text(
                    verdict,
                    style="color:#374151; font-size:14px; margin-top:10px; font-style:italic;",
                )

        with solara.Card("📊 Score Breakdown", style="margin-top:16px;"):
            for key, (label, bar_color) in SCORE_META.items():
                ScoreBar(label, r.get(key, 0), bar_color)
        readiness = r.get("hackathon_readiness", "")
        if readiness:
            with solara.Card("🎯 Hackathon Readiness", style="margin-top:16px;"):
                solara.Text(readiness, style="font-size:14px; line-height:1.7;")

        strengths    = r.get("strengths", [])
        improvements = r.get("improvements", [])
        if strengths or improvements:
            with solara.Row(style="gap:16px; margin-top:16px;"):
                if strengths:
                    with solara.Card(" What's Good", style="flex:1;"):
                        BulletList(strengths, "#10b981")
                if improvements:
                    with solara.Card(" Improvements Needed", style="flex:1;"):
                        BulletList(improvements, "#f59e0b")

        standout  = r.get("standout_files", [])
        problem   = r.get("problem_areas", [])
        if standout or problem:
            with solara.Row(style="gap:16px; margin-top:16px;"):
                if standout:
                    with solara.Card(" Standout Files", style="flex:1;"):
                        BulletList(standout, "#6366f1")
                if problem:
                    with solara.Card(" Problem Areas", style="flex:1;"):
                        BulletList(problem, "#ef4444")

        solara.Button(
            " Judge Another Repo",
            color="primary",
            on_click=reset,
            style="margin-top:24px; width:100%;",
        )


@solara.component
def Page():
    solara.Title("Repo Judge")

    if screen.value == "form":
        FormScreen()
    else:
        ResultsScreen()
