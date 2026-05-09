from pathlib import Path
import solara
import requests
import os
import threading
from solara_app.components import CountdownTerminal

API = os.getenv("API_URL", "http://localhost:8000")

SESSION_STATES = {}

def get_session_state():
    sid = solara.get_session_id()
    if sid not in SESSION_STATES:
        SESSION_STATES[sid] = {
            "student_name": solara.reactive(""),
            "selected_domains": solara.reactive([]),
            "all_domains": solara.reactive([]),
            "setup_error": solara.reactive(""),
            "session_id": solara.reactive(None),
            "questions": solara.reactive([]),
            "user_answers": solara.reactive({}),
            "loading": solara.reactive(False),
            "loading_step": solara.reactive(""),
            "scores": solara.reactive(None),
            "screen": solara.reactive("setup"),
            "initialized": solara.reactive(False),
        }
    return SESSION_STATES[sid]


def load_domains(all_domains, setup_error):
    try:
        r = requests.get(f"{API}/assess/domains", timeout=5)
        r.raise_for_status()
        all_domains.set(r.json())
    except Exception as e:
        setup_error.set(f"Cannot reach backend: {e}")


def _parse_error(r) -> str:
    try:
        return r.json().get("detail", r.text) or r.text
    except Exception:
        return r.text or f"HTTP {r.status_code}"


def _run_generate(sid: str):
    state = SESSION_STATES.get(sid)
    if not state: return
    
    name = state["student_name"].value
    domains = state["selected_domains"].value
    session_id = state["session_id"]
    questions = state["questions"]
    user_answers = state["user_answers"]
    screen = state["screen"]
    setup_error = state["setup_error"]
    loading = state["loading"]
    loading_step = state["loading_step"]

    try:
        loading_step.set(" AI is crafting 15 questions for you…")
        r = requests.post(
            f"{API}/assess/generate-mcq",
            json={"student_name": name, "domains": domains},
            timeout=None,
        )
        if r.status_code == 200:
            data = r.json()
            session_id.set(data["session_id"])
            questions.set(data["questions"])
            user_answers.set({})
            screen.set("quiz")
        else:
            setup_error.set(f" {_parse_error(r)}")
    except Exception as e:
        setup_error.set(f" {e}")
    finally:
        loading.set(False)
        loading_step.set("")


def _run_submit(sid: str):
    state = SESSION_STATES.get(sid)
    if not state: return

    session_id_val = state["session_id"].value
    user_answers_val = state["user_answers"].value
    scores = state["scores"]
    screen = state["screen"]
    setup_error = state["setup_error"]
    loading = state["loading"]
    loading_step = state["loading_step"]

    try:
        loading_step.set("Grading your answers…")
        r = requests.post(
            f"{API}/assess/submit-mcq",
            json={"session_id": session_id_val, "answers": user_answers_val},
            timeout=60,
        )
        if r.status_code == 200:
            scores.set(r.json()["scores"])
            screen.set("results")
        else:
            setup_error.set(f" {_parse_error(r)}")
            screen.set("quiz")
    except Exception as e:
        setup_error.set(f" {e}")
        screen.set("quiz")
    finally:
        loading.set(False)
        loading_step.set("")


DIFF_META = {
    "easy":   (" Easy",   "#34d399", "rgba(16, 185, 129, 0.15)", "rgba(16, 185, 129, 0.3)"),
    "medium": (" Medium", "#f59e0b", "rgba(245, 158, 11, 0.15)", "rgba(245, 158, 11, 0.3)"),
    "hard":   ("Hard",   "#ef4444", "rgba(239, 68, 68, 0.15)",  "rgba(239, 68, 68, 0.3)"),
}


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
                "background:#A4C3B2; border:1px solid rgba(99, 102, 241, 0.1);"
                "color:#1e293b;"
            )
        ),
    )


@solara.component
def QuestionCard(q: dict, index: int, user_answers, select_answer_fn):
    chosen = user_answers.value.get(str(index), "")
    diff = q.get("difficulty", "medium")
    
    with solara.v.Html(
        tag="div",
        class_="assess-glass-card assess-fade-in",
        style_=(
            "background:#A4C3B2; backdrop-filter:blur(20px);"
            "border:1px solid rgba(0, 0, 0, 0.05); border-radius:20px;"
            f"padding:28px; margin-bottom:20px;"
            f"animation-delay:{index * 0.05}s;"
            "box-shadow:0 8px 32px rgba(0, 0, 0, 0.1);"
        ),
    ):
        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;"):
            with solara.v.Html(tag="div", style_="display:flex; align-items:center; gap:12px;"):
                solara.v.Html(
                    tag="div",
                    style_=(
                        "width:36px; height:36px; border-radius:50%;"
                        "background:#A4C3B2;"
                        "display:flex; align-items:center; justify-content:center;"
                        "font-weight:800; font-size:14px; color:#fff; flex-shrink:0;"
                    ),
                    children=[str(index + 1)],
                )
                solara.Text(
                    f"Question {index + 1}",
                    style={"font-size": "13px", "color": "#64748b", "font-weight": "600", "text-transform": "uppercase", "letter-spacing": "1px"},
                )
            DifficultyBadge(diff)

        solara.Text(
            q.get("question", ""),
            style={"font-size": "16px", "font-weight": "600", "color": "#1e293b", "line-height": "1.7", "display": "block", "margin-bottom": "20px"},
        )

        for opt in q.get("options", []):
            letter = opt[0] if opt else ""
            solara.Button(
                opt,
                on_click=lambda l=letter: select_answer_fn(index, l),
                style=(
                    f"width:100%; text-align:left; justify-content:flex-start; text-transform:none;"
                    f"padding:12px 16px; border-radius:12px; font-size:14px; margin-bottom:8px;"
                    f"white-space:pre-wrap; height:auto !important; min-height:48px; line-height:1.5;"
                    f"transition:all 0.3s ease; font-weight:{'700' if chosen == letter else '500'}; "
                    + (
                        "background:linear-gradient(135deg, #7c3aed, #6366f1); border:none; color:#fff;"
                        "box-shadow:0 4px 15px rgba(124, 58, 237, 0.3);"
                        if chosen == letter else
                        "background:A4C3B2; border:1px solid rgba(99, 102, 241, 0.1);"
                        "color:#1e293b;"
                    )
                ),
            )


@solara.component
def SetupScreen(student_name, selected_domains, all_domains, setup_error, loading, loading_step, start_quiz_fn):
    with solara.v.Html(tag="div", style_="max-width:680px; margin:0 auto; padding:40px 24px;"):
        solara.Text("⚡ AI Developer Assessment", style={"font-size": "36px", "font-weight": "900", "color": "#1e293b", "margin-bottom": "16px", "display": "block", "letter-spacing": "-1px"})
        solara.Text(
            "Select a domain to generate an adaptive, 15-question technical exam. "
            "Our AI will grade your responses and calculate your global percentile.",
            style={"font-size": "16px", "color": "#475569", "line-height": "1.6"}
        )

        with solara.v.Html(tag="div", style_="background:#A4C3B2; backdrop-filter:blur(20px); border:1px solid rgba(0,0,0,0.05); border-radius:16px; padding:32px; box-shadow:0 10px 40px rgba(0,0,0,0.1); margin-top:36px;"):
            solara.Text(" Your Details", style={"font-size": "20px", "font-weight": "800", "color": "#0891b2", "margin-bottom": "24px", "display": "block"})
            solara.InputText("Full Name", value=student_name, style="width:100%; margin-bottom:16px;")

            solara.Text("Select a Domain:", style={"font-weight": "700", "font-size": "14px", "color": "#64748b", "margin-bottom": "12px", "display": "block"})

            if not all_domains.value:
                solara.Text("Loading domains…", style={"color": "#94a3b8", "font-style": "italic"})
            else:
                with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:8px;"):
                    for d in all_domains.value:
                        is_sel = (d in selected_domains.value)
                        style = {
                            "border-radius": "12px", "font-weight": "600", "transition": "all 0.3s ease",
                            "background": "linear-gradient(135deg, #00ffcc, #0088ff)", "border": "1px solid rgba(0,255,204,0.1)", "color": "#fff", "box-shadow": "0 2px 12px rgba(0,255,204,0.1)"
                        } if is_sel else {
                            "border-radius": "12px", "font-weight": "600", "transition": "all 0.3s ease",
                            "background": "rgba(0,0,0,0.03)", "border": "1px solid rgba(0,0,0,0.1)", "color": "#64748b"
                        }

                        def create_toggle(dom=d):
                            def toggle():
                                current = list(selected_domains.value)
                                if dom in current:
                                    current.remove(dom)
                                else:
                                    current.append(dom)
                                selected_domains.set(current)
                            return toggle

                        solara.Button(
                            ("✓ " if is_sel else "") + d,
                            on_click=create_toggle(d),
                            color="primary" if is_sel else "default",
                            outlined=not is_sel,
                            small=True,
                            style=style,
                        )

            if selected_domains.value:
                solara.Text(
                    f"Selected: {', '.join(selected_domains.value)}",
                    style={"color": "#0891b2", "font-size": "13px", "margin-top": "8px", "font-weight": "600"},
                )

        if setup_error.value:
            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:16px; background:rgba(239, 68, 68, 0.15);"
                    "border:1px solid rgba(239, 68, 68, 0.3); border-radius:12px; padding:12px 16px;"
                ),
            ):
                solara.Text(setup_error.value, style={"color": "#b91c1c", "font-weight": "600", "font-size": "14px"})

        solara.Button(
            " Start Quiz" if not loading.value else "⏳ Generating questions…",
            color="primary",
            on_click=start_quiz_fn,
            disabled=loading.value,
            attributes={"class": "assess-start-btn"},
            style=(
                "width:100%; margin-top:24px; padding:16px; font-weight:800; font-size:16px;"
                "letter-spacing:1px; border-radius:14px;"
                "background:linear-gradient(135deg, #00ffcc, #0088ff); border:none; color:#fff;"
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
                    loading_step.value or " Working…",
                    style={"color": "#92400e", "font-weight": "600", "font-size": "14px", "display": "block"},
                )
                solara.Text(
                    "The AI is generating your personalised quiz. This may take 1–2 minutes.",
                    style={"color": "#475569", "font-size": "13px", "margin-top": "4px", "display": "block"},
                )


@solara.component
def QuizScreen(questions, user_answers, selected_domains, loading, submit_quiz_fn, select_answer_fn):
    total_q = len(questions.value)
    answered = len(user_answers.value)

    with solara.v.Html(tag="div", style_="max-width:760px; margin:0 auto; padding:24px; text-align:left;"):
        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:12px;"):
            solara.v.Html(
                tag="div",
                children=[f" Quiz: {', '.join(selected_domains.value)}"],
                style_="font-size:24px; font-weight:800; color:#1e293b;",
            )
            solara.v.Html(
                tag="div",
                style_=(
                    "background:#A4C3B2; border:1px solid rgba(0,0,0,0.05);"
                    "border-radius:12px; padding:8px 16px; backdrop-filter:blur(8px);"
                ),
                children=[f" {answered}/{total_q} answered"],
            )

        pct = (answered / total_q * 100) if total_q > 0 else 0
        with solara.v.Html(
            tag="div",
            style_=(
                "background:rgba(0,0,0,0.05); border-radius:9999px; height:8px;"
                "width:100%; overflow:hidden; margin-bottom:28px; margin-top:12px;"
            ),
        ):
            solara.v.Html(tag="div", style_=f"background:linear-gradient(90deg, #00ffcc, #0088ff); height:8px; width:{pct}%; transition:width 0.5s ease;")

        for i, q in enumerate(questions.value):
            QuestionCard(q, i, user_answers, select_answer_fn)

        all_answered = answered >= total_q and total_q > 0
        solara.Button(
            f" Submit Quiz ({answered}/{total_q})" if not all_answered else "📊 Submit Quiz ✓",
            color="primary",
            on_click=submit_quiz_fn,
            disabled=not all_answered or loading.value,
            attributes={"class": "assess-start-btn"},
            style=(
                "width:100%; margin-top:12px; padding:16px; font-weight:800; font-size:16px;"
                "letter-spacing:1px; border-radius:14px;"
                + (
                    "background:linear-gradient(135deg, #00ffcc, #0088ff); border:none; color:#fff;"
                    if all_answered else
                    "background:rgba(0, 0, 0, 0.05); border:none; color:rgba(0,0,0,0.3);"
                    "cursor:not-allowed;"
                )
            ),
        )


import pathlib
solara.Style(pathlib.Path(__file__).parent.parent / 'assets' / 'custom.css')

@solara.component
def SubmittingScreen():
    with solara.v.Html(tag="div", style_="max-width:600px; margin:80px auto; padding:24px;"):
        with solara.v.Html(
            tag="div",
            style_=(
                "text-align:center; padding:48px;"
                "background:#A4C3B2; backdrop-filter:blur(20px);"
                "border:1px solid rgba(0,0,0,0.05); border-radius:20px;"
            ),
        ):
            solara.Text(f"Grading Your Quiz…", style={"font-size": "24px", "font-weight": "800", "color": "#0891b2", "display": "block", "margin-bottom": "12px"})
            solara.Text("Calculating your score and developer percentile. Just a moment!", style={"color": "#475569", "font-size": "15px", "display": "block"})


@solara.component
def ResultsScreen(scores, student_name_val, restart_fn):
    s = scores.value
    if not s:
        return solara.Text("No scores yet.")

    correct, total, pctile = s.get("correct", 0), s.get("total", 15), s.get("percentile", 50)
    details = s.get("details", [])
    pct_score = int((correct / total) * 100) if total > 0 else 0
    color = "#34d399" if pct_score >= 80 else "#f59e0b" if pct_score >= 50 else "#ef4444"

    pctile_msg = (
        f" You're better than {pctile}% of developers worldwide! Elite level!" if pctile >= 90 else
        f" You're better than {pctile}% of developers worldwide! Impressive!" if pctile >= 70 else
        f" You're better than {pctile}% of developers worldwide! Above average!" if pctile >= 50 else
        f" You're better than {pctile}% of developers worldwide. Keep learning!"
    )

    with solara.v.Html(tag="div", style_="max-width:760px; margin:0 auto; padding:40px 24px;"):
        solara.v.Html(
            tag="div",
            children=[f"🎓 Results for {student_name_val}"],
            style_="font-size:30px; font-weight:900; color:#1e293b; margin-bottom:24px;",
        )

        with solara.v.Html(tag="div", style_=f"text-align:center; padding:40px; border-top:4px solid {color}; background:#A4C3B2; backdrop-filter:blur(20px); border-radius:20px; box-shadow:0 12px 40px rgba(0, 0, 0, 0.1); border:1px solid rgba(0,0,0,0.05);"):
            solara.Text("Your Score", style={"color": "#64748b", "font-size": "14px", "text-transform": "uppercase", "letter-spacing": "1px"})
            solara.Text(f"{correct}/{total}", style={"font-size": "64px", "font-weight": "900", "color": color, "line-height": "1.1", "margin": "8px 0", "display": "block", "text-shadow": f"0 0 30px {color}40"})
            solara.Text(f"{pct_score}% correct", style={"color": color, "font-size": "18px", "font-weight": "700", "display": "block", "margin-bottom": "16px"})

        pctile_color = "#0891b2" if pctile >= 70 else "#b45309" if pctile >= 40 else "#be123c"
        with solara.v.Html(tag="div", style_=f"margin-top:20px; text-align:center; padding:32px; background:#A4C3B2; backdrop-filter:blur(20px); border:1px solid rgba(0,0,0,0.05); border-radius:20px; box-shadow:0 8px 32px rgba(0, 0, 0, 0.05);"):
            solara.Text("Developer Percentile", style={"color": "#64748b", "font-size": "13px", "text-transform": "uppercase", "letter-spacing": "1px", "display": "block"})
            solara.Text(f"{pctile}%", style={"font-size": "56px", "font-weight": "900", "color": pctile_color, "display": "block", "margin": "8px 0"})
            solara.Text(pctile_msg, style={"color": "#1e293b", "font-size": "16px", "font-weight": "600", "display": "block"})

        with solara.v.Html(tag="div", style_="margin-top:24px; display:flex; gap:16px; flex-wrap:wrap;"):
            for dk, (l, dc, bg, b) in DIFF_META.items():
                with solara.v.Html(tag="div", style_=f"flex:1; min-width:180px; text-align:center; padding:24px; background:{bg}; border:1px solid {b}; border-radius:16px; backdrop-filter:blur(12px);"):
                    solara.Text(l, style={"font-size": "14px", "font-weight": "700", "color": dc, "display": "block", "margin-bottom": "8px"})
                    solara.Text(f"{s.get(dk+'_correct', 0)}/{s.get(dk+'_total', 0)}", style={"font-size": "32px", "font-weight": "900", "color": dc, "display": "block"})

        if details:
            with solara.v.Html(tag="div", style_="margin-top:32px; padding:28px; border-radius:20px; background:#A4C3B2; backdrop-filter:blur(20px); border:1px solid rgba(0,0,0,0.05); text-align:left;"):
                solara.Text(" Question Review", style={"font-size": "20px", "font-weight": "800", "color": "#0891b2", "display": "block", "margin-bottom": "24px"})
                for d in details:
                    ic = d.get("is_correct", False)
                    bc = "rgba(16, 185, 129, 0.3)" if ic else "rgba(239, 68, 68, 0.3)"
                    bgc = "rgba(16, 185, 129, 0.05)" if ic else "rgba(239, 68, 68, 0.05)"
                    with solara.v.Html(tag="div", style_=f"background:{bgc}; border:1px solid {bc}; border-radius:14px; padding:18px; margin-bottom:14px;"):
                        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"):
                            solara.Text(f"Q{d['index']+1}", style={"font-weight": "800", "font-size": "14px", "color": "#1e293b"})
                            DifficultyBadge(d.get("difficulty", "medium"))
                        solara.Text(d.get("question", ""), style={"font-size": "14px", "color": "#1e293b", "line-height": "1.6", "display": "block", "margin-bottom": "10px"})
                        solara.Text(f"Your answer: {d.get('user_answer','')} {'✓' if ic else '• Correct: '+d.get('correct_answer','')}", style={"font-size": "13px", "color": "#34d399" if ic else "#fca5a5", "font-weight": "600"})

        solara.Button(" Take Another Quiz", color="primary", on_click=restart_fn, style="margin-top:28px; width:100%; padding:16px; font-weight:800; font-size:16px; background:linear-gradient(135deg, #00ffcc, #0088ff); border:none; color:#fff; border-radius:14px;")


@solara.component
def Page():
    solara.Title("MCQ Assessment")
    
    state = get_session_state()
    student_name     = state["student_name"]
    selected_domains = state["selected_domains"]
    all_domains      = state["all_domains"]
    setup_error      = state["setup_error"]
    session_id       = state["session_id"]
    questions        = state["questions"]
    user_answers     = state["user_answers"]
    loading          = state["loading"]
    loading_step     = state["loading_step"]
    scores           = state["scores"]
    screen           = state["screen"]
    initialized      = state["initialized"]

    def start_quiz():
        setup_error.set("")
        name, domains = student_name.value.strip(), selected_domains.value
        if not name: return setup_error.set(" Please enter your name.")
        if not domains: return setup_error.set(" Please select at least one domain.")
        loading.set(True)
        loading_step.set(" Connecting to backend…")
        sid = solara.get_session_id()
        threading.Thread(target=_run_generate, args=(sid,), daemon=True).start()

    def select_answer(qi, letter):
        u = dict(user_answers.value); u[str(qi)] = letter; user_answers.set(u)

    def submit_quiz():
        loading.set(True); screen.set("submitting")
        sid = solara.get_session_id()
        threading.Thread(target=_run_submit, args=(sid,), daemon=True).start()

    def restart():
        screen.set("setup"); session_id.set(None); questions.set([]); user_answers.set({}); scores.set(None); student_name.set(""); selected_domains.set([]); setup_error.set(""); loading.set(False)

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

    solara.use_effect(lambda: load_domains(all_domains, setup_error), [])
    solara.HTML(tag="style", unsafe_innerHTML=".v-application, .v-application--wrap, .v-main, .v-main__wrap, .v-sheet { background-color: #A4C3B2 !important; background: #A4C3B2 !important; } .theme--light.v-sheet { background-color: #A4C3B2 !important; } body { background-color: #A4C3B2 !important; background: #A4C3B2 !important; margin: 0; min-height: 100vh; } .v-text-field input { color: #0891b2 !important; font-family: 'JetBrains Mono', monospace !important; }")

    with solara.v.Html(tag="div", style_="min-height:100vh; background:#A4C3B2; font-family:'Inter',sans-serif; color:#1e293b; position:relative; overflow:hidden;"):
        for _ in range(3): solara.v.Html(tag="div", attributes={"class": "assess-particle", "style": "background:rgba(0,0,0,0.05);"})
        solara.v.Html(tag="div", attributes={"class": "assess-grid", "style": "background-image: linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px);"})
        with solara.v.Html(tag="div", style_="position:relative; z-index:1;"):
            if screen.value == "setup": SetupScreen(student_name, selected_domains, all_domains, setup_error, loading, loading_step, start_quiz)
            elif screen.value == "quiz": QuizScreen(questions, user_answers, selected_domains, loading, submit_quiz, select_answer)
            elif screen.value == "submitting": SubmittingScreen()
            else: ResultsScreen(scores, student_name.value, restart)
