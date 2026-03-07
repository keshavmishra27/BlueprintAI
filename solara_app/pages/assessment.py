import solara
import requests
import os
import time

API = os.getenv("API_URL", "http://localhost:8000")

# Setup screen
student_name    = solara.reactive("")
selected_domains= solara.reactive([])
all_domains     = solara.reactive([])
setup_error     = solara.reactive("")

session_id         = solara.reactive(None)
messages           = solara.reactive([])   # [{role, content}
chat_loading       = solara.reactive(False)
session_start_time = solara.reactive(0.0)  # time.time() when chat started
SESSION_DURATION   = 300

# Results screen
scores          = solara.reactive(None)
scoring         = solara.reactive(False)

screen          = solara.reactive("setup")

def load_domains():
    try:
        r = requests.get(f"{API}/assess/domains", timeout=5)
        r.raise_for_status()
        all_domains.set(r.json())
    except Exception as e:
        setup_error.set(f"❌ Cannot reach backend: {e}")


def _parse_error(r) -> str:
    """Safely extract an error message from a response, never crashes."""
    try:
        return r.json().get("detail", r.text) or r.text
    except Exception:
        return r.text or f"HTTP {r.status_code}"


def toggle_domain(domain: str):
    current = list(selected_domains.value)
    if domain in current:
        current.remove(domain)
    else:
        current.append(domain)
    selected_domains.set(current)


def start_assessment():
    setup_error.set("")
    if not student_name.value.strip():
        setup_error.set("⚠️ Please enter your name.")
        return
    if not selected_domains.value:
        setup_error.set("⚠️ Please select at least one domain.")
        return

    chat_loading.set(True)
    try:
        r = requests.post(
            f"{API}/assess/start",
            json={"student_name": student_name.value.strip(), "domains": selected_domains.value},
            timeout=120,   # Ollama needs ~30-60s on first call to load model
        )
        if r.status_code != 200:
            setup_error.set(f"❌ {_parse_error(r)}")
            return
        data = r.json()
        session_id.set(data["session_id"])
        messages.set([{"role": "agent", "content": data["message"]}])
        session_start_time.set(time.time())   # record start — no thread needed
        screen.set("chat")
    except Exception as e:
        setup_error.set(f"❌ {e}")
    finally:
        chat_loading.set(False)


def send_message(text: str):
    """Send a student message and append the agent reply."""
    if not text.strip() or chat_loading.value:
        return

    # Add student message immediately
    updated = list(messages.value)
    updated.append({"role": "student", "content": text.strip()})
    messages.set(updated)

    chat_loading.set(True)
    try:
        r = requests.post(
            f"{API}/assess/chat",
            json={"session_id": session_id.value, "student_message": text.strip()},
            timeout=120,   # Ollama inference can take 20-60s
        )
        if r.status_code == 200:
            reply = r.json()["agent_reply"]
            updated2 = list(messages.value)
            updated2.append({"role": "agent", "content": reply})
            messages.set(updated2)
        else:
            detail = _parse_error(r)
            updated2 = list(messages.value)
            updated2.append({"role": "agent", "content": f"⚠️ Error: {detail}"})
            messages.set(updated2)
    except Exception as e:
        updated2 = list(messages.value)
        updated2.append({"role": "agent", "content": f"⚠️ Connection error: {e}"})
        messages.set(updated2)
    finally:
        chat_loading.set(False)


def end_and_score():
    scoring.set(True)
    screen.set("results")
    try:
        r = requests.post(f"{API}/assess/score/{session_id.value}", timeout=180)  # CrewAI crew takes ~60-120s
        if r.status_code == 200:
            scores.set(r.json()["scores"])
        else:
            scores.set({"error": _parse_error(r)})
    except Exception as e:
        scores.set({"error": str(e)})
    finally:
        scoring.set(False)


def restart():
    screen.set("setup")
    session_id.set(None)
    messages.set([])
    scores.set(None)
    session_start_time.set(0.0)
    student_name.set("")
    selected_domains.set([])
    setup_error.set("")



# Sub components

SCORE_COLORS = {
    "domain_knowledge": "#a78bfa",
    "creativity":       "#f59e0b",
    "communication":    "#34d399",
    "engagement":       "#60a5fa",
}
SCORE_LABELS = {
    "domain_knowledge": "🧠 Domain Knowledge",
    "creativity":       "🎨 Creativity",
    "communication":    "💬 Communication",
    "engagement":       "⚡ Engagement",
}


@solara.component
def ScoreBar(label: str, value: int, color: str):
    pct = min(100, (value / 25) * 100)
    with solara.v.Html(tag="div", style_="margin-bottom:16px;"):
        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;"):
            solara.Text(label, style={"font-weight": "600", "font-size": "14px", "color": "#e2e8f0"})
            solara.Text(f"{value}/25", style={"color": color, "font-weight": "700", "font-size": "14px"})
        with solara.v.Html(tag="div", style_="background:rgba(255,255,255,0.1); border-radius:9999px; height:10px; width:100%; overflow:hidden;"):
            solara.v.Html(
                tag="div",
                style_=(
                    f"background:linear-gradient(90deg, {color}, {color}aa);"
                    f"border-radius:9999px; height:10px;"
                    f"width:{pct}%; transition:width 1s ease;"
                    f"box-shadow:0 0 12px {color}60;"
                ),
                children=[],
            )


@solara.component
def ChatBubble(role: str, content: str):
    is_agent = role == "agent"
    if is_agent:
        align = "flex-start"
        bg = "rgba(15, 23, 42, 0.8)"
        border = "1px solid rgba(139, 92, 246, 0.3)"
        color = "#e2e8f0"
        label_text = "🤖 AI Interviewer"
        label_color = "#a78bfa"
        shadow = "0 4px 20px rgba(139, 92, 246, 0.1)"
    else:
        align = "flex-end"
        bg = "linear-gradient(135deg, #6366f1, #8b5cf6)"
        border = "none"
        color = "#ffffff"
        label_text = "👤 You"
        label_color = "rgba(255,255,255,0.7)"
        shadow = "0 4px 20px rgba(99, 102, 241, 0.3)"

    with solara.v.Html(tag="div", style_=f"display:flex; justify-content:{align}; margin:8px 0;"):
        with solara.v.Html(
            tag="div",
            style_=(
                f"max-width:78%; background:{bg}; color:{color};"
                f"padding:14px 18px; border-radius:16px; font-size:14px; line-height:1.6;"
                f"border:{border}; box-shadow:{shadow}; backdrop-filter:blur(8px);"
            )
        ):
            solara.Text(label_text, style={"font-size": "11px", "color": label_color, "margin-bottom": "6px", "font-weight": "700", "text-transform": "uppercase", "letter-spacing": "0.5px"})
            solara.Text(content, style={"white-space": "pre-wrap"})


@solara.component
def TimerBadge():
    # Local state for display update
    now, set_now = solara.use_state(time.time())

    def update_time():
        import threading
        if screen.value == "chat":
            set_now(time.time())
            threading.Timer(1.0, update_time).start()

    solara.use_effect(update_time, [])

    if session_start_time.value == 0:
        return solara.Text("⏱️ 05:00", style={"font-weight": "700", "font-size": "18px", "color": "#a78bfa"})

    elapsed = now - session_start_time.value
    t = max(0, int(SESSION_DURATION - elapsed))
    
    if t == 0 and screen.value == "chat":
        end_and_score()

    mins, secs = divmod(t, 60)
    color = "#ef4444" if t < 60 else "#a78bfa"
    anim = "animation: pulse 1s ease-in-out infinite;" if t < 60 else ""
    
    with solara.v.Html(
        tag="div",
        style_=(
            f"background:rgba(15, 23, 42, 0.8); border:1px solid {color}40;"
            f"border-radius:12px; padding:8px 16px; backdrop-filter:blur(8px);"
            f"box-shadow:0 0 15px {color}20; {anim}"
        )
    ):
        solara.Text(
            f"⏱️ {mins:02d}:{secs:02d}",
            style={"font-weight": "700", "font-size": "20px", "color": color, "font-family": "'JetBrains Mono', monospace"},
        )


# Pages

@solara.component
def SetupScreen():
    with solara.v.Html(tag="div", style_="max-width:680px; margin:0 auto; padding:40px 24px;"):
        # Title with entrance animation
        solara.v.Html(
            tag="div",
            attributes={"class": "assess-fade-in"},
            children=["📝 Student Productivity Assessment"],
            style_="font-size:34px; font-weight:900; color:#f1f5f9; margin-bottom:12px; text-shadow:0 2px 20px rgba(139, 92, 246, 0.4);",
        )
        solara.v.Html(
            tag="div",
            attributes={"class": "assess-fade-in"},
            children=["Chat with an AI interviewer for 5 minutes. You'll receive a detailed productivity score."],
            style_="font-size:16px; color:rgba(255,255,255,0.7); line-height:1.6; margin-bottom:36px;",
        )

        # Form card
        with solara.v.Html(
            tag="div",
            attributes={"class": "assess-glass-card"},
            style_=(
                "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
                "border:1px solid rgba(139, 92, 246, 0.2); border-radius:20px;"
                "padding:32px; box-shadow:0 12px 40px rgba(0, 0, 0, 0.3);"
            )
        ):
            solara.Text("🎯 Your Details", style={"font-size": "20px", "font-weight": "800", "color": "#a78bfa", "margin-bottom": "24px", "display": "block"})
            
            solara.InputText("Full Name", value=student_name, style="width:100%; margin-bottom:16px;")

            solara.Text("Select Domain(s):", style={"font-weight": "700", "font-size": "14px", "color": "rgba(255,255,255,0.7)", "margin-bottom": "12px", "display": "block"})
            
            if not all_domains.value:
                solara.Text("Loading domains…", style={"color": "rgba(255,255,255,0.5)", "font-style": "italic"})
            else:
                with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:8px;"):
                    for d in all_domains.value:
                        is_sel = d in selected_domains.value
                        solara.Button(
                            ("✓ " if is_sel else "") + d,
                            on_click=lambda dom=d: toggle_domain(dom),
                            color="primary" if is_sel else "default",
                            outlined=not is_sel,
                            small=True,
                            style=f"border-radius:12px; font-weight:600; transition:all 0.3s ease; {'background:linear-gradient(135deg, #7c3aed, #6366f1); border:none; color:#fff; box-shadow:0 2px 12px rgba(124, 58, 237, 0.3);' if is_sel else 'background:rgba(139, 92, 246, 0.08); color:#94a3b8; border:1px solid rgba(139, 92, 246, 0.25);'}"
                        )

            if selected_domains.value:
                solara.Text(
                    f"Selected: {', '.join(selected_domains.value)}",
                    style={"color": "#a78bfa", "font-size": "13px", "margin-top": "8px", "font-weight": "600"},
                )

        if setup_error.value:
            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:16px; background:rgba(239, 68, 68, 0.15);"
                    "border:1px solid rgba(239, 68, 68, 0.3); border-radius:12px;"
                    "padding:12px 16px;"
                )
            ):
                solara.Text(setup_error.value, style={"color": "#fca5a5", "font-weight": "600", "font-size": "14px"})

        solara.Button(
            "🚀 Start Assessment (5 min)",
            color="primary",
            on_click=start_assessment,
            disabled=chat_loading.value,
            attributes={"class": "assess-start-btn"},
            style=(
                "width:100%; margin-top:24px; padding:16px; font-weight:800; font-size:16px;"
                "letter-spacing:1px; border-radius:14px;"
                "background:linear-gradient(135deg, #7c3aed, #6366f1); border:none; color:#fff;"
            ),
        )

        if chat_loading.value:
            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:20px; background:rgba(245, 158, 11, 0.12);"
                    "border-left:3px solid #f59e0b; padding:14px 18px; border-radius:0 12px 12px 0;"
                )
            ):
                solara.Text("⏳ Starting session… AI is warming up, please wait.", style={"color": "#fcd34d", "font-weight": "600", "font-size": "14px"})


@solara.component
def ChatScreen():
    # Local state for the input
    input_text, set_input_text = solara.use_state("")

    def handle_send():
        if input_text.strip() and not chat_loading.value:
            text = input_text.strip()
            set_input_text("")
            send_message(text)

    with solara.v.Html(tag="div", style_="max-width:800px; margin:0 auto; padding:24px;"):
        # Header
        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;"):
            solara.v.Html(
                tag="div",
                children=[f"💬 Chatting as {student_name.value}"],
                style_="font-size:22px; font-weight:800; color:#f1f5f9;",
            )
            TimerBadge()

        solara.Text(
            f"Domains: {', '.join(selected_domains.value)}",
            style={"color": "rgba(255,255,255,0.5)", "font-size": "13px", "margin-bottom": "16px", "display": "block"},
        )

        # Chat history
        with solara.v.Html(
            tag="div",
            style_=(
                "min-height:380px; max-height:460px; overflow-y:auto;"
                "background:rgba(15, 23, 42, 0.5); backdrop-filter:blur(16px);"
                "border:1px solid rgba(139, 92, 246, 0.15); border-radius:16px;"
                "padding:20px; box-shadow:0 8px 32px rgba(0, 0, 0, 0.2);"
            )
        ):
            for msg in messages.value:
                ChatBubble(msg["role"], msg["content"])
            if chat_loading.value:
                with solara.v.Html(
                    tag="div",
                    attributes={"class": "assess-thinking"},
                    style_=(
                        "display:flex; align-items:center; gap:10px; padding:10px 16px;"
                        "background:rgba(139, 92, 246, 0.08); border-radius:12px;"
                        "border:1px solid rgba(139, 92, 246, 0.15); width:fit-content; margin-top:8px;"
                    )
                ):
                    solara.Text("🤖 AI is thinking…", style={"color": "#a78bfa", "font-size": "13px", "font-weight": "600"})

        # Input row
        with solara.v.Html(tag="div", style_="display:flex; gap:12px; margin-top:16px; align-items:center;"):
            with solara.v.Html(tag="div", style_="flex:1;"):
                solara.InputText(
                    "Type your answer…",
                    value=input_text,
                    on_value=set_input_text,
                    continuous_update=True,
                    style="width:100%;",
                )
            solara.Button(
                "Send ➤",
                color="primary",
                on_click=handle_send,
                disabled=chat_loading.value or not input_text.strip(),
                style=(
                    "padding:10px 24px; font-weight:700; border-radius:12px;"
                    "background:linear-gradient(135deg, #7c3aed, #6366f1); border:none; color:#fff;"
                    "transition:all 0.3s ease;"
                ),
            )

        solara.Button(
            "🏁 End & Get Score",
            color="error",
            outlined=True,
            on_click=end_and_score,
            style=(
                "margin-top:12px; padding:10px 24px; font-weight:700; border-radius:12px;"
                "background:rgba(239, 68, 68, 0.1); border:1px solid rgba(239, 68, 68, 0.3);"
                "color:#fca5a5; transition:all 0.3s ease;"
            ),
        )


@solara.component
def ResultsScreen():
    with solara.v.Html(tag="div", style_="max-width:700px; margin:0 auto; padding:40px 24px;"):
        solara.v.Html(
            tag="div",
            attributes={"class": "assess-fade-in"},
            children=[f"🎓 Results for {student_name.value}"],
            style_="font-size:30px; font-weight:900; color:#f1f5f9; margin-bottom:24px; text-shadow:0 2px 20px rgba(139, 92, 246, 0.4);",
        )

        if scoring.value:
            with solara.v.Html(
                tag="div",
                attributes={"class": "assess-glass-card"},
                style_=(
                    "text-align:center; padding:48px;"
                    "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
                    "border:1px solid rgba(139, 92, 246, 0.2); border-radius:20px;"
                )
            ):
                solara.Text("⏳ Analyzing your conversation…", style={"font-size": "22px", "font-weight": "800", "color": "#a78bfa", "display": "block", "margin-bottom": "12px"})
                solara.Text(
                    "Our AI crew is reviewing your answers. This typically takes 20–40 seconds.",
                    style={"color": "rgba(255,255,255,0.6)", "font-size": "15px", "display": "block"},
                )
            return

        if not scores.value:
            solara.Text("No scores yet.", style={"color": "rgba(255,255,255,0.5)"})
            return

        if "error" in scores.value:
            with solara.v.Html(
                tag="div",
                style_=(
                    "background:rgba(239, 68, 68, 0.15); border:1px solid rgba(239, 68, 68, 0.3);"
                    "border-radius:16px; padding:20px;"
                )
            ):
                solara.Text(f"❌ {scores.value['error']}", style={"color": "#fca5a5", "font-size": "15px"})
            solara.Button("🔄 Try Again", on_click=end_and_score, style="margin-top:12px;")
            return

        total = scores.value.get("total", 0)
        color = "#34d399" if total >= 75 else "#f59e0b" if total >= 50 else "#ef4444"
        grade = "Excellent 🌟" if total >= 80 else "Good 👍" if total >= 60 else "Needs Improvement 📚"

        # Total score card
        with solara.v.Html(
            tag="div",
            attributes={"class": "assess-fade-in"},
            style_=(
                f"text-align:center; padding:40px; border-top:4px solid {color};"
                "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
                "border-radius:20px; box-shadow:0 12px 40px rgba(0, 0, 0, 0.3);"
                f"border:1px solid {color}33;"
            )
        ):
            solara.Text("Total Score", style={"color": "rgba(255,255,255,0.5)", "font-size": "14px", "text-transform": "uppercase", "letter-spacing": "1px"})
            solara.Text(
                f"{total}/100",
                style={"font-size": "56px", "font-weight": "900", "color": color, "line-height": "1.1", "margin": "8px 0", "display": "block",
                       "text-shadow": f"0 0 30px {color}40"},
            )
            solara.Text(grade, style={"color": color, "font-size": "18px", "font-weight": "700"})

        # Dimension bars
        with solara.v.Html(
            tag="div",
            attributes={"class": "assess-glass-card"},
            style_=(
                "margin-top:24px; padding:28px; border-radius:20px;"
                "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
                "border:1px solid rgba(139, 92, 246, 0.2); box-shadow:0 8px 32px rgba(0, 0, 0, 0.2);"
            )
        ):
            solara.Text("📊 Score Breakdown", style={"font-size": "18px", "font-weight": "800", "color": "#a78bfa", "display": "block", "margin-bottom": "20px"})
            for key, label in SCORE_LABELS.items():
                val = scores.value.get(key, 0)
                ScoreBar(label, val, SCORE_COLORS[key])

        # Summary
        summary = scores.value.get("summary", "")
        if summary:
            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:24px; padding:24px; border-radius:20px;"
                    "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
                    "border:1px solid rgba(139, 92, 246, 0.2);"
                )
            ):
                solara.Text("📋 Feedback", style={"font-size": "18px", "font-weight": "800", "color": "#a78bfa", "display": "block", "margin-bottom": "12px"})
                solara.Text(summary, style={"font-size": "14px", "line-height": "1.8", "color": "#e2e8f0"})

        # Strengths & Areas to improve
        strengths = scores.value.get("strengths", [])
        improvements = scores.value.get("areas_to_improve", [])

        if strengths or improvements:
            with solara.v.Html(tag="div", style_="display:flex; gap:20px; margin-top:24px; flex-wrap:wrap;"):
                if strengths:
                    with solara.v.Html(
                        tag="div",
                        style_=(
                            "flex:1; min-width:280px; padding:24px; border-radius:16px;"
                            "background:rgba(16, 185, 129, 0.08); border:1px solid rgba(16, 185, 129, 0.25);"
                            "backdrop-filter:blur(12px);"
                        )
                    ):
                        solara.Text("💪 Strengths", style={"font-size": "16px", "font-weight": "800", "color": "#34d399", "display": "block", "margin-bottom": "14px"})
                        for s in strengths:
                            with solara.v.Html(tag="div", style_="display:flex; align-items:flex-start; gap:8px; margin-bottom:8px;"):
                                solara.Text("✅", style={"flex-shrink": "0"})
                                solara.Text(s, style={"font-size": "14px", "color": "#e2e8f0", "line-height": "1.5"})
                if improvements:
                    with solara.v.Html(
                        tag="div",
                        style_=(
                            "flex:1; min-width:280px; padding:24px; border-radius:16px;"
                            "background:rgba(245, 158, 11, 0.08); border:1px solid rgba(245, 158, 11, 0.25);"
                            "backdrop-filter:blur(12px);"
                        )
                    ):
                        solara.Text("📈 Areas to Improve", style={"font-size": "16px", "font-weight": "800", "color": "#f59e0b", "display": "block", "margin-bottom": "14px"})
                        for a in improvements:
                            with solara.v.Html(tag="div", style_="display:flex; align-items:flex-start; gap:8px; margin-bottom:8px;"):
                                solara.Text("🎯", style={"flex-shrink": "0"})
                                solara.Text(a, style={"font-size": "14px", "color": "#e2e8f0", "line-height": "1.5"})

        solara.Button(
            "🔁 Start New Assessment",
            color="primary",
            on_click=restart,
            style=(
                "margin-top:28px; width:100%; padding:16px; font-weight:800; font-size:16px;"
                "letter-spacing:1px; border-radius:14px;"
                "background:linear-gradient(135deg, #7c3aed, #6366f1); border:none; color:#fff;"
            ),
        )


# Main Page component

@solara.component
def Page():
    solara.Title("Assessment")

    # Premium Assessment page CSS
    solara.HTML(tag="style", unsafe_innerHTML="""
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=JetBrains+Mono:wght@700&display=swap');

        .v-application, .v-application--wrap, .v-main__wrap {
            background: transparent !important;
        }

        /* === ANIMATED GRADIENT BG === */
        @keyframes assessGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* === FLOATING PARTICLES === */
        .assess-particle {
            position: absolute;
            border-radius: 50%;
            pointer-events: none;
            opacity: 0;
            animation: assessFloat 18s ease-in-out infinite;
        }
        .assess-particle:nth-child(1) {
            width: 350px; height: 350px;
            background: radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, transparent 70%);
            top: -5%; left: -10%;
            animation-delay: 0s;
        }
        .assess-particle:nth-child(2) {
            width: 280px; height: 280px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.10) 0%, transparent 70%);
            top: 40%; right: -8%;
            animation-delay: -5s;
        }
        .assess-particle:nth-child(3) {
            width: 200px; height: 200px;
            background: radial-gradient(circle, rgba(167, 139, 250, 0.08) 0%, transparent 70%);
            bottom: 10%; left: 15%;
            animation-delay: -10s;
        }
        @keyframes assessFloat {
            0%, 100% { opacity: 0; transform: translateY(0) scale(1); }
            25% { opacity: 1; }
            50% { opacity: 1; transform: translateY(-40px) scale(1.15); }
            75% { opacity: 1; }
        }

        /* === SHOOTING STARS === */
        .assess-star {
            position: absolute;
            width: 120px;
            height: 2px;
            background: linear-gradient(90deg, transparent, #8b5cf6, #a78bfa, transparent);
            border-radius: 2px;
            opacity: 0;
            pointer-events: none;
        }
        .assess-star:nth-child(4) {
            top: 18%; right: 5%;
            animation: assessShoot 4s linear 1s infinite;
        }
        .assess-star:nth-child(5) {
            top: 55%; right: 15%;
            animation: assessShoot 5s linear 3.5s infinite;
        }
        @keyframes assessShoot {
            0% { opacity: 0; transform: translateX(0) rotate(-35deg); }
            5% { opacity: 1; }
            30% { opacity: 0; transform: translateX(-350px) rotate(-35deg); }
            100% { opacity: 0; }
        }

        /* === GRID OVERLAY === */
        .assess-grid {
            position: absolute;
            inset: 0;
            background-image:
                linear-gradient(rgba(139, 92, 246, 0.06) 1px, transparent 1px),
                linear-gradient(90deg, rgba(139, 92, 246, 0.06) 1px, transparent 1px);
            background-size: 60px 60px;
            pointer-events: none;
            opacity: 0.5;
            animation: assessGridFade 8s ease-in-out infinite alternate;
        }
        @keyframes assessGridFade {
            0% { opacity: 0.3; }
            100% { opacity: 0.6; }
        }

        /* === GLASS CARD === */
        .assess-glass-card {
            transition: transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease;
        }
        .assess-glass-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 30px rgba(139, 92, 246, 0.1);
            border-color: rgba(139, 92, 246, 0.4) !important;
        }

        /* === ENTRANCE ANIMATION === */
        .assess-fade-in {
            animation: assessFadeSlide 0.6s ease-out both;
        }
        @keyframes assessFadeSlide {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* === BUTTON EFFECTS === */
        .assess-start-btn {
            box-shadow: 0 0 20px rgba(124, 58, 237, 0.3), 0 0 40px rgba(124, 58, 237, 0.1);
            animation: assessBtnPulse 3s ease-in-out infinite;
            transition: all 0.3s ease !important;
        }
        .assess-start-btn:hover {
            animation: none !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 0 30px rgba(124, 58, 237, 0.4), 0 0 60px rgba(124, 58, 237, 0.2), 0 8px 30px rgba(0,0,0,0.3) !important;
            filter: brightness(1.15) !important;
        }
        .assess-start-btn:active {
            transform: translateY(0) scale(0.98) !important;
        }
        @keyframes assessBtnPulse {
            0%, 100% { box-shadow: 0 0 15px rgba(124, 58, 237, 0.3), 0 0 30px rgba(124, 58, 237, 0.1); }
            50% { box-shadow: 0 0 25px rgba(124, 58, 237, 0.4), 0 0 50px rgba(124, 58, 237, 0.2), 0 0 80px rgba(124, 58, 237, 0.1); }
        }

        /* All buttons hover glow */
        .v-btn:hover {
            transform: translateY(-2px) scale(1.03) !important;
            filter: brightness(1.15) !important;
        }
        .v-btn:active {
            transform: translateY(0) scale(0.97) !important;
        }

        /* === THINKING ANIMATION === */
        .assess-thinking {
            animation: assessThinkPulse 1.5s ease-in-out infinite;
        }
        @keyframes assessThinkPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        /* === TIMER PULSE === */
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        /* === CUSTOM SCROLLBAR === */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.3);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #7c3aed, #6366f1);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, #8b5cf6, #818cf8);
        }

        /* === SMOOTH SCROLL === */
        html {
            scroll-behavior: smooth;
        }
    """)

    solara.use_effect(load_domains, [])

    # Main wrapper with animated gradient
    with solara.v.Html(
        tag="div",
        style_=(
            "min-height:100vh;"
            "position:relative; overflow:hidden;"
            "background: linear-gradient(-45deg, #0a0a1a, #1a0a2e, #150e30, #0d1025, #0a0a1a);"
            "background-size: 400% 400%;"
            "animation: assessGradient 20s ease infinite;"
            "font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
            "color:#e2e8f0;"
            "padding-bottom:60px;"
            "box-sizing:border-box;"
        )
    ):
        # Floating particles
        for _ in range(3):
            solara.v.Html(tag="div", attributes={"class": "assess-particle"})
        # Shooting stars
        for _ in range(2):
            solara.v.Html(tag="div", attributes={"class": "assess-star"})
        # Grid overlay
        solara.v.Html(tag="div", attributes={"class": "assess-grid"})

        # Content (z-indexed above particles)
        with solara.v.Html(tag="div", style_="position:relative; z-index:1;"):
            if screen.value == "setup":
                SetupScreen()
            elif screen.value == "chat":
                ChatScreen()
            else:
                ResultsScreen()
