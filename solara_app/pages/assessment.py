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
    "domain_knowledge": "#6366f1",
    "creativity":       "#f59e0b",
    "communication":    "#10b981",
    "engagement":       "#3b82f6",
}
SCORE_LABELS = {
    "domain_knowledge": "Domain Knowledge",
    "creativity":       "Creativity",
    "communication":    "Communication",
    "engagement":       "Engagement",
}


@solara.component
def ScoreBar(label: str, value: int, color: str):
    pct = min(100, (value / 25) * 100)
    with solara.Column(style="margin-bottom:12px;"):
        with solara.Row(justify="space-between"):
            solara.Text(label, style="font-weight:600; font-size:14px;")
            solara.Text(f"{value}/25", style=f"color:{color}; font-weight:700;")
        # Progress bar
        with solara.Div(style="background:#e5e7eb; border-radius:9999px; height:10px; width:100%;"):
            with solara.Div(style=(
                f"background:{color}; border-radius:9999px; height:10px;"
                f"width:{pct}%; transition:width 0.8s ease;"
            )):
                pass


@solara.component
def ChatBubble(role: str, content: str):
    is_agent = role == "agent"
    align = "flex-start" if is_agent else "flex-end"
    bg    = "#f3f4f6" if is_agent else "#6366f1"
    color = "#1f2937" if is_agent else "#ffffff"
    label = "🤖 Agent" if is_agent else "👤 You"

    with solara.Div(style=f"display:flex; justify-content:{align}; margin:6px 0;"):
        with solara.Div(
            style=(
                f"max-width:75%; background:{bg}; color:{color};"
                f"padding:10px 14px; border-radius:16px; font-size:14px; line-height:1.5;"
            )
        ):
            solara.Text(label, style=f"font-size:11px; opacity:0.6; margin-bottom:4px;")
            solara.Text(content)


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
        return solara.Text("⏱️ 05:00", style="font-weight:700; font-size:18px; color:#6366f1;")

    elapsed = now - session_start_time.value
    t = max(0, int(SESSION_DURATION - elapsed))
    
    if t == 0 and screen.value == "chat":
        end_and_score()

    mins, secs = divmod(t, 60)
    color = "#ef4444" if t < 60 else "#6366f1"
    
    return solara.Text(
        f"⏱️ {mins:02d}:{secs:02d}",
        style=f"font-weight:700; font-size:18px; color:{color};",
    )


# Pages

@solara.component
def SetupScreen():
    with solara.Column(style="max-width:640px; margin:0 auto; padding:32px;"):
        solara.Markdown("# 📝 Student Productivity Assessment")
        solara.Markdown(
            "Chat with an AI interviewer for **5 minutes**. "
            "You'll receive a productivity score based on your answers."
        )

        with solara.Card("Your Details"):
            solara.InputText("Full Name", value=student_name, style="width:100%;")

            solara.Markdown("**Select Domain(s):**")
            if not all_domains.value:
                solara.Text("Loading domains…", style="color:#888;")
            else:
                # Show domains as toggle chips
                with solara.Div(style="display:flex; flex-wrap:wrap; gap:8px; margin:8px 0;"):
                    for d in all_domains.value:
                        is_sel = d in selected_domains.value
                        solara.Button(
                            ("✓ " if is_sel else "") + d,
                            on_click=lambda dom=d: toggle_domain(dom),
                            color="primary" if is_sel else "default",
                            outlined=not is_sel,
                            small=True,
                        )

            if selected_domains.value:
                solara.Text(
                    f"Selected: {', '.join(selected_domains.value)}",
                    style="color:#6366f1; font-size:13px; margin-top:4px;",
                )

        if setup_error.value:
            solara.Text(setup_error.value, style="color:#ef4444;")

        solara.Button(
            "🚀 Start Assessment (5 min)",
            color="primary",
            on_click=start_assessment,
            disabled=chat_loading.value,
            style="width:100%; margin-top:8px;",
        )

        if chat_loading.value:
            solara.Text("Starting session… please wait.", style="color:#888;")


@solara.component
def ChatScreen():
    # Local state for the input
    input_text, set_input_text = solara.use_state("")

    def handle_send():
        if input_text.strip() and not chat_loading.value:
            text = input_text.strip()
            set_input_text("")
            send_message(text)

    with solara.Column(style="max-width:760px; margin:0 auto; padding:24px;"):
        with solara.Row(justify="space-between"):
            solara.Markdown(f"### 💬 Chatting as **{student_name.value}**")
            TimerBadge()

        solara.Text(
            f"Domains: {', '.join(selected_domains.value)}",
            style="color:#888; font-size:13px; margin-bottom:12px;",
        )

        # Chat history
        with solara.Card(style="min-height:350px; max-height:450px; overflow-y:auto;"):
            for msg in messages.value:
                ChatBubble(msg["role"], msg["content"])
            if chat_loading.value:
                solara.Text("🤖 Agent is thinking…", style="color:#888; font-size:13px;")

        # Input row
        with solara.Row(style="margin-top:12px; gap:8px;"):
            solara.InputText(
                "Type your answer and press Send…",
                value=input_text,
                on_value=set_input_text,
                continuous_update=True,
                style="flex:1;",
            )
            solara.Button(
                "Send ➤",
                color="primary",
                on_click=handle_send,
                disabled=chat_loading.value or not input_text.strip(),
            )

        solara.Button(
            "🏁 End & Get Score",
            color="error",
            outlined=True,
            on_click=end_and_score,
            style="margin-top:8px;",
        )


@solara.component
def ResultsScreen():
    with solara.Column(style="max-width:640px; margin:0 auto; padding:32px;"):
        solara.Markdown(f"# 🎓 Results for {student_name.value}")

        if scoring.value:
            solara.Markdown("### ⏳ Analyzing your conversation…")
            solara.Text(
                "Our AI crew is reviewing your answers. This takes 20–40 seconds.",
                style="color:#888;",
            )
            return

        if not scores.value:
            solara.Text("No scores yet.", style="color:#888;")
            return

        if "error" in scores.value:
            solara.Text(f"❌ {scores.value['error']}", style="color:#ef4444;")
            solara.Button("🔄 Try Again", on_click=end_and_score)
            return

        total = scores.value.get("total", 0)
        color = "#10b981" if total >= 75 else "#f59e0b" if total >= 50 else "#ef4444"

        # Total score ring
        with solara.Card(style=f"text-align:center; padding:24px; border-top:4px solid {color};"):
            solara.Text("Total Score", style="color:#888; font-size:14px;")
            solara.Text(
                f"{total}/100",
                style=f"font-size:48px; font-weight:900; color:{color};",
            )
            grade = "Excellent 🌟" if total >= 80 else "Good 👍" if total >= 60 else "Needs Improvement 📚"
            solara.Text(grade, style=f"color:{color}; font-size:16px;")

        # Dimension bars
        with solara.Card("Score Breakdown", style="margin-top:16px;"):
            for key, label in SCORE_LABELS.items():
                val = scores.value.get(key, 0)
                ScoreBar(label, val, SCORE_COLORS[key])

        # Summary
        summary = scores.value.get("summary", "")
        if summary:
            with solara.Card("📋 Feedback", style="margin-top:16px;"):
                solara.Text(summary, style="font-size:14px; line-height:1.7;")

        # Strengths & Areas to improve
        strengths = scores.value.get("strengths", [])
        improvements = scores.value.get("areas_to_improve", [])

        if strengths or improvements:
            with solara.Row(style="gap:16px; margin-top:16px;"):
                if strengths:
                    with solara.Card("💪 Strengths", style="flex:1;"):
                        for s in strengths:
                            solara.Text(f"✅ {s}", style="font-size:13px;")
                if improvements:
                    with solara.Card("📈 Areas to Improve", style="flex:1;"):
                        for a in improvements:
                            solara.Text(f"🎯 {a}", style="font-size:13px;")

        solara.Button(
            "🔁 Start New Assessment",
            color="primary",
            on_click=restart,
            style="margin-top:16px; width:100%;",
        )


# Main Page component

@solara.component
def Page():
    solara.Title("Assessment")

    solara.use_effect(load_domains, [])

    if screen.value == "setup":
        SetupScreen()
    elif screen.value == "chat":
        ChatScreen()
    else:
        ResultsScreen()
