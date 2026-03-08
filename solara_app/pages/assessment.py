"""
assessment.py  —  Solara page for MCQ-based assessment.
User picks a domain → AI generates 15 MCQs → user answers → gets score + percentile.
"""

import solara
import requests
import os
import threading

API = os.getenv("API_URL", "http://localhost:8000")

# ── Reactive state ─────────────────────────────────────────────────
student_name     = solara.reactive("")
selected_domain  = solara.reactive("")
all_domains      = solara.reactive([])
setup_error      = solara.reactive("")

session_id       = solara.reactive(None)
questions        = solara.reactive([])     # list of question dicts
user_answers     = solara.reactive({})     # {"0": "A", "1": "C", ...}
loading          = solara.reactive(False)
loading_step     = solara.reactive("")

scores           = solara.reactive(None)
screen           = solara.reactive("setup")   # "setup" | "quiz" | "results"


# ── Actions ────────────────────────────────────────────────────────

def load_domains():
    try:
        r = requests.get(f"{API}/assess/domains", timeout=5)
        r.raise_for_status()
        all_domains.set(r.json())
    except Exception as e:
        setup_error.set(f"❌ Cannot reach backend: {e}")


def _parse_error(r) -> str:
    try:
        return r.json().get("detail", r.text) or r.text
    except Exception:
        return r.text or f"HTTP {r.status_code}"


def _run_generate(name: str, domain: str):
    """Background thread — calls the backend to generate MCQs."""
    try:
        loading_step.set("🧠 AI is crafting 15 questions for you…")
        r = requests.post(
            f"{API}/assess/generate-mcq",
            json={"student_name": name, "domain": domain},
            timeout=None,
        )
        if r.status_code == 200:
            data = r.json()
            session_id.set(data["session_id"])
            questions.set(data["questions"])
            user_answers.set({})
            screen.set("quiz")
        else:
            setup_error.set(f"❌ {_parse_error(r)}")
    except Exception as e:
        setup_error.set(f"❌ {e}")
    finally:
        loading.set(False)
        loading_step.set("")


def start_quiz():
    setup_error.set("")
    name = student_name.value.strip()
    domain = selected_domain.value.strip()
    if not name:
        setup_error.set("⚠️ Please enter your name.")
        return
    if not domain:
        setup_error.set("⚠️ Please select a domain.")
        return

    loading.set(True)
    loading_step.set("🔌 Connecting to backend…")
    threading.Thread(target=_run_generate, args=(name, domain), daemon=True).start()


def select_answer(q_index: int, letter: str):
    updated = dict(user_answers.value)
    updated[str(q_index)] = letter
    user_answers.set(updated)


def _run_submit():
    """Background thread — submits answers for grading."""
    try:
        loading_step.set("📊 Grading your answers…")
        r = requests.post(
            f"{API}/assess/submit-mcq",
            json={"session_id": session_id.value, "answers": user_answers.value},
            timeout=60,
        )
        if r.status_code == 200:
            scores.set(r.json()["scores"])
            screen.set("results")
        else:
            setup_error.set(f"❌ {_parse_error(r)}")
            screen.set("quiz")
    except Exception as e:
        setup_error.set(f"❌ {e}")
        screen.set("quiz")
    finally:
        loading.set(False)
        loading_step.set("")


def submit_quiz():
    loading.set(True)
    screen.set("submitting")
    threading.Thread(target=_run_submit, daemon=True).start()


def restart():
    screen.set("setup")
    session_id.set(None)
    questions.set([])
    user_answers.set({})
    scores.set(None)
    student_name.set("")
    selected_domain.set("")
    setup_error.set("")
    loading.set(False)


# ── Difficulty helpers ─────────────────────────────────────────────

DIFF_META = {
    "easy":   ("🟢 Easy",   "#34d399", "rgba(16, 185, 129, 0.15)", "rgba(16, 185, 129, 0.3)"),
    "medium": ("🟡 Medium", "#f59e0b", "rgba(245, 158, 11, 0.15)", "rgba(245, 158, 11, 0.3)"),
    "hard":   ("🔴 Hard",   "#ef4444", "rgba(239, 68, 68, 0.15)",  "rgba(239, 68, 68, 0.3)"),
}


# ── Components ─────────────────────────────────────────────────────

@solara.component
def DifficultyBadge(difficulty: str):
    label, color, bg, border = DIFF_META.get(difficulty, DIFF_META["medium"])
    solara.v.Html(
        tag="span",
        style_=(
            f"display:inline-block; background:{bg}; border:1px solid {border};"
            f"color:{color}; font-size:11px; font-weight:700; padding:3px 10px;"
            "border-radius:20px; text-transform:uppercase; letter-spacing:0.5px;"
        ),
        children=[label],
    )


@solara.component
def OptionButton(q_index: int, letter: str, text: str, is_selected: bool):
    solara.Button(
        text,
        on_click=lambda l=letter: select_answer(q_index, l),
        style=(
            f"width:100%; text-align:left; justify-content:flex-start; text-transform:none;"
            f"padding:12px 16px; border-radius:12px; font-size:14px; margin-bottom:8px;"
            f"white-space:pre-wrap; height:auto !important; min-height:48px; line-height:1.5;"
            f"transition:all 0.3s ease; font-weight:{'700' if is_selected else '500'}; "
            + (
                "background:linear-gradient(135deg, #7c3aed, #6366f1); border:none; color:#fff;"
                "box-shadow:0 4px 15px rgba(124, 58, 237, 0.3);"
                if is_selected else
                "background:rgba(139, 92, 246, 0.08); border:1px solid rgba(139, 92, 246, 0.2);"
                "color:#e2e8f0;"
            )
        ),
    )


@solara.component
def QuestionCard(q: dict, index: int):
    chosen = user_answers.value.get(str(index), "")
    diff = q.get("difficulty", "medium")
    
    with solara.v.Html(
        tag="div",
        class_="assess-glass-card assess-fade-in",
        style_=(
            "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
            "border:1px solid rgba(139, 92, 246, 0.2); border-radius:20px;"
            f"padding:28px; margin-bottom:20px;"
            f"animation-delay:{index * 0.05}s;"
            "box-shadow:0 8px 32px rgba(0, 0, 0, 0.2);"
        ),
    ):
        # Header: number + difficulty badge
        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;"):
            with solara.v.Html(tag="div", style_="display:flex; align-items:center; gap:12px;"):
                solara.v.Html(
                    tag="div",
                    style_=(
                        "width:36px; height:36px; border-radius:50%;"
                        "background:linear-gradient(135deg, #7c3aed, #6366f1);"
                        "display:flex; align-items:center; justify-content:center;"
                        "font-weight:800; font-size:14px; color:#fff; flex-shrink:0;"
                    ),
                    children=[str(index + 1)],
                )
                solara.Text(
                    f"Question {index + 1}",
                    style={"font-size": "13px", "color": "rgba(255,255,255,0.5)", "font-weight": "600", "text-transform": "uppercase", "letter-spacing": "1px"},
                )
            DifficultyBadge(diff)

        # Question text
        solara.Text(
            q.get("question", ""),
            style={"font-size": "16px", "font-weight": "600", "color": "#f1f5f9", "line-height": "1.7", "display": "block", "margin-bottom": "20px"},
        )

        # Options
        for opt in q.get("options", []):
            letter = opt[0] if opt else ""
            OptionButton(
                q_index=index,
                letter=letter,
                text=opt,
                is_selected=(chosen == letter),
            )


@solara.component
def SetupScreen():
    with solara.v.Html(tag="div", style_="max-width:680px; margin:0 auto; padding:40px 24px;"):
        solara.v.Html(
            tag="div",
            attributes={"class": "assess-fade-in"},
            children=["📝 MCQ Assessment"],
            style_="font-size:34px; font-weight:900; color:#f1f5f9; margin-bottom:12px; text-shadow:0 2px 20px rgba(139, 92, 246, 0.4);",
        )
        solara.v.Html(
            tag="div",
            attributes={"class": "assess-fade-in"},
            children=["15 MCQ questions • 5 Easy • 5 Medium • 5 Hard • See how you rank among developers worldwide"],
            style_="font-size:16px; color:rgba(255,255,255,0.7); line-height:1.6; margin-bottom:36px;",
        )

        with solara.v.Html(
            tag="div",
            attributes={"class": "assess-glass-card"},
            style_=(
                "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
                "border:1px solid rgba(139, 92, 246, 0.2); border-radius:20px;"
                "padding:32px; box-shadow:0 12px 40px rgba(0, 0, 0, 0.3);"
            ),
        ):
            solara.Text("🎯 Your Details", style={"font-size": "20px", "font-weight": "800", "color": "#a78bfa", "margin-bottom": "24px", "display": "block"})
            solara.InputText("Full Name", value=student_name, style="width:100%; margin-bottom:16px;")

            solara.Text("Select a Domain:", style={"font-weight": "700", "font-size": "14px", "color": "rgba(255,255,255,0.7)", "margin-bottom": "12px", "display": "block"})

            if not all_domains.value:
                solara.Text("Loading domains…", style={"color": "rgba(255,255,255,0.5)", "font-style": "italic"})
            else:
                with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:8px;"):
                    for d in all_domains.value:
                        is_sel = (d == selected_domain.value)
                        solara.Button(
                            ("✓ " if is_sel else "") + d,
                            on_click=lambda dom=d: selected_domain.set(dom),
                            color="primary" if is_sel else "default",
                            outlined=not is_sel,
                            small=True,
                            style=(
                                f"border-radius:12px; font-weight:600; transition:all 0.3s ease; "
                                + (
                                    "background:linear-gradient(135deg, #7c3aed, #6366f1); border:none; color:#fff; "
                                    "box-shadow:0 2px 12px rgba(124, 58, 237, 0.3);"
                                    if is_sel else
                                    "background:rgba(139, 92, 246, 0.08); color:#94a3b8; border:1px solid rgba(139, 92, 246, 0.25);"
                                )
                            ),
                        )

            if selected_domain.value:
                solara.Text(
                    f"Selected: {selected_domain.value}",
                    style={"color": "#a78bfa", "font-size": "13px", "margin-top": "8px", "font-weight": "600"},
                )

        if setup_error.value:
            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:16px; background:rgba(239, 68, 68, 0.15);"
                    "border:1px solid rgba(239, 68, 68, 0.3); border-radius:12px; padding:12px 16px;"
                ),
            ):
                solara.Text(setup_error.value, style={"color": "#fca5a5", "font-weight": "600", "font-size": "14px"})

        solara.Button(
            "🚀 Start Quiz" if not loading.value else "⏳ Generating questions…",
            color="primary",
            on_click=start_quiz,
            disabled=loading.value,
            attributes={"class": "assess-start-btn"},
            style=(
                "width:100%; margin-top:24px; padding:16px; font-weight:800; font-size:16px;"
                "letter-spacing:1px; border-radius:14px;"
                "background:linear-gradient(135deg, #7c3aed, #6366f1); border:none; color:#fff;"
            ),
        )

        if loading.value:
            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:20px; background:rgba(245, 158, 11, 0.12);"
                    "border-left:3px solid #f59e0b; padding:14px 18px; border-radius:0 12px 12px 0;"
                ),
            ):
                solara.Text(
                    loading_step.value or "⏳ Working…",
                    style={"color": "#fcd34d", "font-weight": "600", "font-size": "14px", "display": "block"},
                )
                solara.Text(
                    "The AI is generating your personalised quiz. This may take 1–2 minutes.",
                    style={"color": "rgba(255,255,255,0.6)", "font-size": "13px", "margin-top": "4px", "display": "block"},
                )


@solara.component
def QuizScreen():
    total_q = len(questions.value)
    answered = len(user_answers.value)

    with solara.v.Html(tag="div", style_="max-width:760px; margin:0 auto; padding:24px;"):
        # Header
        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:12px;"):
            solara.v.Html(
                tag="div",
                children=[f"📝 Quiz: {selected_domain.value}"],
                style_="font-size:24px; font-weight:800; color:#f1f5f9;",
            )
            solara.v.Html(
                tag="div",
                style_=(
                    "background:rgba(15, 23, 42, 0.8); border:1px solid rgba(139, 92, 246, 0.3);"
                    "border-radius:12px; padding:8px 16px; backdrop-filter:blur(8px);"
                ),
                children=[f"✅ {answered}/{total_q} answered"],
            )

        # Progress bar
        pct = (answered / total_q * 100) if total_q > 0 else 0
        with solara.v.Html(
            tag="div",
            style_=(
                "background:rgba(255,255,255,0.1); border-radius:9999px; height:8px;"
                "width:100%; overflow:hidden; margin-bottom:28px; margin-top:12px;"
            ),
        ):
            solara.v.Html(
                tag="div",
                style_=(
                    f"background:linear-gradient(90deg, #7c3aed, #a78bfa); height:8px;"
                    f"border-radius:9999px; width:{pct}%; transition:width 0.5s ease;"
                ),
                children=[],
            )

        # Questions
        for i, q in enumerate(questions.value):
            QuestionCard(q, i)

        # Submit button
        all_answered = answered >= total_q and total_q > 0
        solara.Button(
            f"📊 Submit Quiz ({answered}/{total_q})" if not all_answered else "📊 Submit Quiz ✓",
            color="primary",
            on_click=submit_quiz,
            disabled=not all_answered or loading.value,
            attributes={"class": "assess-start-btn"},
            style=(
                "width:100%; margin-top:12px; padding:16px; font-weight:800; font-size:16px;"
                "letter-spacing:1px; border-radius:14px;"
                + (
                    "background:linear-gradient(135deg, #7c3aed, #6366f1); border:none; color:#fff;"
                    if all_answered else
                    "background:rgba(139, 92, 246, 0.2); border:none; color:rgba(255,255,255,0.4);"
                    "cursor:not-allowed;"
                )
            ),
        )


@solara.component
def SubmittingScreen():
    with solara.v.Html(tag="div", style_="max-width:600px; margin:80px auto; padding:24px;"):
        with solara.v.Html(
            tag="div",
            attributes={"class": "assess-glass-card"},
            style_=(
                "text-align:center; padding:48px;"
                "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
                "border:1px solid rgba(139, 92, 246, 0.2); border-radius:20px;"
            ),
        ):
            solara.Text("📊 Grading Your Quiz…", style={"font-size": "24px", "font-weight": "800", "color": "#a78bfa", "display": "block", "margin-bottom": "12px"})
            solara.Text(
                "Calculating your score and developer percentile. Just a moment!",
                style={"color": "rgba(255,255,255,0.6)", "font-size": "15px", "display": "block"},
            )


@solara.component
def ResultsScreen():
    s = scores.value
    if not s:
        solara.Text("No scores yet.", style={"color": "rgba(255,255,255,0.5)"})
        return

    correct  = s.get("correct", 0)
    total    = s.get("total", 15)
    pctile   = s.get("percentile", 50)
    details  = s.get("details", [])

    pct_score = int((correct / total) * 100) if total > 0 else 0
    color = "#34d399" if pct_score >= 80 else "#f59e0b" if pct_score >= 50 else "#ef4444"

    # Percentile message
    if pctile >= 90:
        pctile_msg = f"🔥 You're better than {pctile}% of developers worldwide! Elite level!"
    elif pctile >= 70:
        pctile_msg = f"🚀 You're better than {pctile}% of developers worldwide! Impressive!"
    elif pctile >= 50:
        pctile_msg = f"💪 You're better than {pctile}% of developers worldwide! Above average!"
    else:
        pctile_msg = f"📚 You're better than {pctile}% of developers worldwide. Keep learning!"

    with solara.v.Html(tag="div", style_="max-width:760px; margin:0 auto; padding:40px 24px;"):
        solara.v.Html(
            tag="div",
            attributes={"class": "assess-fade-in"},
            children=[f"🎓 Results for {student_name.value}"],
            style_="font-size:30px; font-weight:900; color:#f1f5f9; margin-bottom:24px; text-shadow:0 2px 20px rgba(139, 92, 246, 0.4);",
        )

        # ── Score Card ──
        with solara.v.Html(
            tag="div",
            attributes={"class": "assess-fade-in"},
            style_=(
                f"text-align:center; padding:40px; border-top:4px solid {color};"
                "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
                "border-radius:20px; box-shadow:0 12px 40px rgba(0, 0, 0, 0.3);"
                f"border:1px solid {color}33;"
            ),
        ):
            solara.Text("Your Score", style={"color": "rgba(255,255,255,0.5)", "font-size": "14px", "text-transform": "uppercase", "letter-spacing": "1px"})
            solara.Text(
                f"{correct}/{total}",
                style={
                    "font-size": "64px", "font-weight": "900", "color": color,
                    "line-height": "1.1", "margin": "8px 0", "display": "block",
                    "text-shadow": f"0 0 30px {color}40",
                },
            )
            solara.Text(
                f"{pct_score}% correct",
                style={"color": color, "font-size": "18px", "font-weight": "700", "display": "block", "margin-bottom": "16px"},
            )

        # ── Percentile Card ──
        pctile_color = "#a78bfa" if pctile >= 70 else "#f59e0b" if pctile >= 40 else "#ef4444"
        with solara.v.Html(
            tag="div",
            attributes={"class": "assess-fade-in"},
            style_=(
                "margin-top:20px; text-align:center; padding:32px;"
                "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
                f"border:1px solid {pctile_color}33; border-radius:20px;"
                "box-shadow:0 8px 32px rgba(0, 0, 0, 0.2);"
            ),
        ):
            solara.Text(
                "Developer Percentile",
                style={"color": "rgba(255,255,255,0.5)", "font-size": "13px", "text-transform": "uppercase", "letter-spacing": "1px", "display": "block"},
            )
            solara.Text(
                f"{pctile}%",
                style={
                    "font-size": "56px", "font-weight": "900", "color": pctile_color,
                    "display": "block", "margin": "8px 0",
                    "text-shadow": f"0 0 30px {pctile_color}40",
                },
            )
            solara.Text(
                pctile_msg,
                style={"color": "#e2e8f0", "font-size": "16px", "font-weight": "600", "display": "block"},
            )

        # ── Difficulty Breakdown ──
        with solara.v.Html(
            tag="div",
            style_=(
                "margin-top:24px; display:flex; gap:16px; flex-wrap:wrap;"
            ),
        ):
            for diff_key, (label, diff_color, bg, border) in DIFF_META.items():
                c_key = f"{diff_key}_correct"
                t_key = f"{diff_key}_total"
                dc = s.get(c_key, 0)
                dt = s.get(t_key, 0)
                with solara.v.Html(
                    tag="div",
                    style_=(
                        f"flex:1; min-width:180px; text-align:center; padding:24px;"
                        f"background:{bg}; border:1px solid {border}; border-radius:16px;"
                        "backdrop-filter:blur(12px);"
                    ),
                ):
                    solara.Text(label, style={"font-size": "14px", "font-weight": "700", "color": diff_color, "display": "block", "margin-bottom": "8px"})
                    solara.Text(
                        f"{dc}/{dt}",
                        style={"font-size": "32px", "font-weight": "900", "color": diff_color, "display": "block"},
                    )

        # ── Question Review ──
        if details:
            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:32px; padding:28px; border-radius:20px;"
                    "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
                    "border:1px solid rgba(139, 92, 246, 0.2);"
                ),
            ):
                solara.Text("📋 Question Review", style={"font-size": "20px", "font-weight": "800", "color": "#a78bfa", "display": "block", "margin-bottom": "24px"})

                for d in details:
                    is_correct = d.get("is_correct", False)
                    diff = d.get("difficulty", "medium")
                    _, diff_color, _, _ = DIFF_META.get(diff, DIFF_META["medium"])
                    icon = "✅" if is_correct else "❌"
                    border_c = "rgba(16, 185, 129, 0.3)" if is_correct else "rgba(239, 68, 68, 0.3)"
                    bg_c = "rgba(16, 185, 129, 0.05)" if is_correct else "rgba(239, 68, 68, 0.05)"

                    with solara.v.Html(
                        tag="div",
                        style_=(
                            f"background:{bg_c}; border:1px solid {border_c};"
                            "border-radius:14px; padding:18px; margin-bottom:14px;"
                        ),
                    ):
                        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"):
                            with solara.v.Html(tag="div", style_="display:flex; align-items:center; gap:8px;"):
                                solara.Text(f"{icon} Q{d['index'] + 1}", style={"font-weight": "800", "font-size": "14px", "color": "#e2e8f0"})
                                DifficultyBadge(diff)

                        solara.Text(
                            d.get("question", ""),
                            style={"font-size": "14px", "color": "#e2e8f0", "line-height": "1.6", "display": "block", "margin-bottom": "10px"},
                        )

                        user_ans = d.get("user_answer", "")
                        correct_ans = d.get("correct_answer", "")

                        if not is_correct:
                            solara.Text(
                                f"Your answer: {user_ans}  •  Correct: {correct_ans}",
                                style={"font-size": "13px", "color": "#fca5a5", "font-weight": "600", "display": "block"},
                            )
                        else:
                            solara.Text(
                                f"Your answer: {user_ans} ✓",
                                style={"font-size": "13px", "color": "#34d399", "font-weight": "600", "display": "block"},
                            )

        # Restart button
        solara.Button(
            "🔁 Take Another Quiz",
            color="primary",
            on_click=restart,
            style=(
                "margin-top:28px; width:100%; padding:16px; font-weight:800; font-size:16px;"
                "letter-spacing:1px; border-radius:14px;"
                "background:linear-gradient(135deg, #7c3aed, #6366f1); border:none; color:#fff;"
            ),
        )


# ── Main Page ──────────────────────────────────────────────────────

@solara.component
def Page():
    solara.Title("MCQ Assessment")

    with solara.v.Html(tag="div"):
        solara.HTML(tag="style", unsafe_innerHTML="""
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=JetBrains+Mono:wght@700&display=swap');

            .v-application, .v-application--wrap, .v-main__wrap {
                background: transparent !important;
            }

        @keyframes assessGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .assess-particle {
            position: absolute; border-radius: 50%; pointer-events: none; opacity: 0;
            animation: assessFloat 18s ease-in-out infinite;
        }
        .assess-particle:nth-child(1) {
            width:350px; height:350px;
            background: radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, transparent 70%);
            top:-5%; left:-10%; animation-delay:0s;
        }
        .assess-particle:nth-child(2) {
            width:280px; height:280px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.10) 0%, transparent 70%);
            top:40%; right:-8%; animation-delay:-5s;
        }
        .assess-particle:nth-child(3) {
            width:200px; height:200px;
            background: radial-gradient(circle, rgba(167, 139, 250, 0.08) 0%, transparent 70%);
            bottom:10%; left:15%; animation-delay:-10s;
        }
        @keyframes assessFloat {
            0%, 100% { opacity:0; transform:translateY(0) scale(1); }
            25% { opacity:1; }
            50% { opacity:1; transform:translateY(-40px) scale(1.15); }
            75% { opacity:1; }
        }

        .assess-star {
            position:absolute; width:120px; height:2px;
            background:linear-gradient(90deg, transparent, #8b5cf6, #a78bfa, transparent);
            border-radius:2px; opacity:0; pointer-events:none;
        }
        .assess-star:nth-child(4) { top:18%; right:5%; animation: assessShoot 4s linear 1s infinite; }
        .assess-star:nth-child(5) { top:55%; right:15%; animation: assessShoot 5s linear 3.5s infinite; }
        @keyframes assessShoot {
            0% { opacity:0; transform:translateX(0) rotate(-35deg); }
            5% { opacity:1; }
            30% { opacity:0; transform:translateX(-350px) rotate(-35deg); }
            100% { opacity:0; }
        }

        .assess-grid {
            position:absolute; inset:0;
            background-image:
                linear-gradient(rgba(139, 92, 246, 0.06) 1px, transparent 1px),
                linear-gradient(90deg, rgba(139, 92, 246, 0.06) 1px, transparent 1px);
            background-size:60px 60px; pointer-events:none; opacity:0.5;
            animation: assessGridFade 8s ease-in-out infinite alternate;
        }
        @keyframes assessGridFade { 0% { opacity:0.3; } 100% { opacity:0.6; } }

        .assess-glass-card {
            transition: transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease;
        }
        .assess-glass-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.3), 0 0 20px rgba(139, 92, 246, 0.08);
            border-color: rgba(139, 92, 246, 0.35) !important;
        }

        .assess-fade-in { animation: assessFadeSlide 0.6s ease-out both; }
        @keyframes assessFadeSlide {
            from { opacity:0; transform:translateY(20px); }
            to { opacity:1; transform:translateY(0); }
        }

        .assess-start-btn {
            box-shadow: 0 0 20px rgba(124, 58, 237, 0.3);
            animation: assessBtnPulse 3s ease-in-out infinite;
            transition: all 0.3s ease !important;
        }
        .assess-start-btn:hover {
            animation: none !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 0 30px rgba(124, 58, 237, 0.4), 0 8px 30px rgba(0,0,0,0.3) !important;
            filter: brightness(1.15) !important;
        }
        @keyframes assessBtnPulse {
            0%, 100% { box-shadow: 0 0 15px rgba(124, 58, 237, 0.3); }
            50% { box-shadow: 0 0 25px rgba(124, 58, 237, 0.4), 0 0 50px rgba(124, 58, 237, 0.15); }
        }

        ::-webkit-scrollbar { width:8px; }
        ::-webkit-scrollbar-track { background:rgba(15, 23, 42, 0.3); border-radius:4px; }
        ::-webkit-scrollbar { width:8px; }
        ::-webkit-scrollbar-track { background:rgba(15, 23, 42, 0.3); border-radius:4px; }
        ::-webkit-scrollbar-thumb { background:linear-gradient(180deg, #7c3aed, #6366f1); border-radius:4px; }
        ::-webkit-scrollbar-thumb:hover { background:linear-gradient(180deg, #8b5cf6, #818cf8); }
        html { scroll-behavior: smooth; }
        """)

        solara.use_effect(load_domains, [])

        with solara.v.Html(
            tag="div",
            style_=(
                "min-height:100vh; position:relative; overflow:hidden;"
                "background: linear-gradient(-45deg, #0a0a1a, #1a0a2e, #150e30, #0d1025, #0a0a1a);"
                "background-size: 400% 400%;"
                "animation: assessGradient 20s ease infinite;"
                "font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
                "color:#e2e8f0; padding-bottom:60px; box-sizing:border-box;"
            ),
        ):
            for _ in range(3):
                solara.v.Html(tag="div", attributes={"class": "assess-particle"})
            for _ in range(2):
                solara.v.Html(tag="div", attributes={"class": "assess-star"})
            solara.v.Html(tag="div", attributes={"class": "assess-grid"})

            with solara.v.Html(tag="div", style_="position:relative; z-index:1;"):
                if screen.value == "setup":
                    SetupScreen()
                elif screen.value == "quiz":
                    QuizScreen()
                elif screen.value == "submitting":
                    SubmittingScreen()
                else:
                    ResultsScreen()
