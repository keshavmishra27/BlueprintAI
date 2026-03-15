from pathlib import Path
import solara
import requests
import os
from typing import List

API = os.getenv("API_URL", "http://localhost:8000")

# ── Persistent Session State ────────────────────────────────────────

SESSION_STATES = {}

def get_session_state():
    sid = solara.get_session_id()
    if sid not in SESSION_STATES:
        SESSION_STATES[sid] = {
            "domains": solara.reactive([]),
            "selected_domain": solara.reactive(None),
            "members_in_domain": solara.reactive([]),
            "all_by_domain": solara.reactive([]),
            "name_input": solara.reactive(""),
            "category_input": solara.reactive(""),
            "new_member_domains": solara.reactive([]),
            "status_msg": solara.reactive(""),
            "loading": solara.reactive(False),
            "is_authorized": solara.reactive(False),
            "terminal_password": solara.reactive(""),
            "terminal_error": solara.reactive(""),
        }
    return SESSION_STATES[sid]


# Data fetchers

def fetch_domains(sid: str):
    state = SESSION_STATES.get(sid)
    if not state: return
    try:
        r = requests.get(f"{API}/members/domains", timeout=5)
        state["domains"].set(r.json())
    except Exception as e:
        state["status_msg"].set(f"❌ Could not load domains: {e}")


def fetch_for_domain(sid: str, domain_id: int):
    state = SESSION_STATES.get(sid)
    if not state: return
    state["loading"].set(True)
    try:
        r = requests.get(f"{API}/members/", params={"domain_id": domain_id}, timeout=5)
        state["members_in_domain"].set(r.json())
    except Exception as e:
        state["status_msg"].set(f"❌ {e}")
    finally:
        state["loading"].set(False)


def fetch_all_by_domain(sid: str):
    state = SESSION_STATES.get(sid)
    if not state: return
    state["loading"].set(True)
    try:
        r = requests.get(f"{API}/members/by-domain", timeout=5)
        state["all_by_domain"].set(r.json())
    except Exception as e:
        state["status_msg"].set(f"❌ {e}")
    finally:
        state["loading"].set(False)


def refresh(sid: str):
    """Re-fetch whatever view is currently active."""
    state = SESSION_STATES.get(sid)
    if not state: return
    state["status_msg"].set("")
    if state["selected_domain"].value:
        fetch_for_domain(sid, state["selected_domain"].value["id"])
    else:
        fetch_all_by_domain(sid)


def select_domain(sid: str, domain):
    """Called when user clicks a domain chip."""
    state = SESSION_STATES.get(sid)
    if not state: return
    state["selected_domain"].set(domain)
    state["status_msg"].set("")
    if domain:
        fetch_for_domain(sid, domain["id"])


def clear_domain(sid: str):
    state = SESSION_STATES.get(sid)
    if not state: return
    state["selected_domain"].set(None)
    fetch_all_by_domain(sid)


def add_member(sid: str):
    state = SESSION_STATES.get(sid)
    if not state: return
    
    name_input = state["name_input"]
    category_input = state["category_input"]
    new_member_domains = state["new_member_domains"]
    status_msg = state["status_msg"]
    loading = state["loading"]

    if not name_input.value.strip() or not category_input.value.strip():
        status_msg.set("⚠️ Please fill in both Name and Category.")
        return
    loading.set(True)
    try:
        body = {
            "name": name_input.value.strip(),
            "category": category_input.value.strip(),
            "domain_ids": new_member_domains.value,
        }
        r = requests.post(f"{API}/members/", json=body, timeout=5)
        if r.status_code == 200:
            d = r.json()
            domain_names = ", ".join(x["name"] for x in d.get("domains", []))
            msg = f"✅ '{d['name']}' added!"
            if domain_names:
                msg += f" Domains: {domain_names}"
            status_msg.set(msg)
            name_input.set("")
            category_input.set("")
            new_member_domains.set([])
            refresh(sid)
        else:
            status_msg.set(f"❌ {r.json().get('detail', r.text)}")
    except Exception as e:
        status_msg.set(f"❌ {e}")
    finally:
        loading.set(False)


def delete_member(sid: str, member_id: int, member_name: str):
    state = SESSION_STATES.get(sid)
    if not state: return
    try:
        r = requests.delete(f"{API}/members/{member_id}", timeout=5)
        if r.status_code == 200:
            state["status_msg"].set(f"🗑️ '{member_name}' deleted.")
            refresh(sid)
        else:
            state["status_msg"].set(f"❌ {r.text}")
    except Exception as e:
        state["status_msg"].set(f"❌ {e}")


# Sub components

CATEGORY_COLOR = {
    "senior":       "#38bdf8",
    "intermediate": "#a78bfa",
    "junior":       "#5eead4",
}

# Domain-specific themes: each domain gets its own background & accent
DOMAIN_THEMES = {
    "default": {
        "gradient": "linear-gradient(-45deg, #0a0e1a, #0f172a, #1e1b4b, #0c1e3a, #0a0e1a)",
        "accent": "#38bdf8",
        "glow": "rgba(56, 189, 248, 0.3)",
        "particle1": "rgba(56, 189, 248, 0.15)",
        "particle2": "rgba(139, 92, 246, 0.15)",
        "particle3": "rgba(20, 184, 166, 0.12)",
        "star_color": "#38bdf8, #6366f1",
        "btn_gradient": "linear-gradient(135deg, #0ea5e9, #6366f1)",
        "chip_active": "linear-gradient(135deg, #0ea5e9, #6366f1)",
    },
    "web devolopment": {
        "gradient": "linear-gradient(-45deg, #0a1a0a, #0d2818, #1a3a1a, #0a2a14, #061208)",
        "accent": "#4ade80",
        "glow": "rgba(74, 222, 128, 0.3)",
        "particle1": "rgba(74, 222, 128, 0.15)",
        "particle2": "rgba(34, 197, 94, 0.12)",
        "particle3": "rgba(16, 185, 129, 0.1)",
        "star_color": "#4ade80, #22c55e",
        "btn_gradient": "linear-gradient(135deg, #22c55e, #059669)",
        "chip_active": "linear-gradient(135deg, #22c55e, #059669)",
    },
    "app devolopment": {
        "gradient": "linear-gradient(-45deg, #1a0a2e, #2d1b69, #4c1d95, #1e1b4b, #0f0720)",
        "accent": "#c084fc",
        "glow": "rgba(192, 132, 252, 0.3)",
        "particle1": "rgba(192, 132, 252, 0.15)",
        "particle2": "rgba(168, 85, 247, 0.12)",
        "particle3": "rgba(249, 115, 22, 0.1)",
        "star_color": "#c084fc, #f97316",
        "btn_gradient": "linear-gradient(135deg, #a855f7, #f97316)",
        "chip_active": "linear-gradient(135deg, #a855f7, #f97316)",
    },
    "machine learning": {
        "gradient": "linear-gradient(-45deg, #0a1520, #0c1e2e, #162d3d, #1a3545, #0d1f2d)",
        "accent": "#22d3ee",
        "glow": "rgba(34, 211, 238, 0.3)",
        "particle1": "rgba(34, 211, 238, 0.15)",
        "particle2": "rgba(6, 182, 212, 0.12)",
        "particle3": "rgba(148, 163, 184, 0.1)",
        "star_color": "#22d3ee, #94a3b8",
        "btn_gradient": "linear-gradient(135deg, #06b6d4, #475569)",
        "chip_active": "linear-gradient(135deg, #06b6d4, #475569)",
    },
    "agentic ai": {
        "gradient": "linear-gradient(-45deg, #0a0a1a, #1a0a2e, #2e0a4a, #1a1040, #0a0520)",
        "accent": "#e879f9",
        "glow": "rgba(232, 121, 249, 0.3)",
        "particle1": "rgba(232, 121, 249, 0.15)",
        "particle2": "rgba(217, 70, 239, 0.12)",
        "particle3": "rgba(168, 85, 247, 0.1)",
        "star_color": "#e879f9, #a855f7",
        "btn_gradient": "linear-gradient(135deg, #d946ef, #7c3aed)",
        "chip_active": "linear-gradient(135deg, #d946ef, #7c3aed)",
    },
    "cloud computing": {
        "gradient": "linear-gradient(-45deg, #0a1628, #0e2a4a, #1e3a5f, #0f2740, #071220)",
        "accent": "#60a5fa",
        "glow": "rgba(96, 165, 250, 0.3)",
        "particle1": "rgba(96, 165, 250, 0.15)",
        "particle2": "rgba(59, 130, 246, 0.12)",
        "particle3": "rgba(147, 197, 253, 0.1)",
        "star_color": "#60a5fa, #93c5fd",
        "btn_gradient": "linear-gradient(135deg, #3b82f6, #1d4ed8)",
        "chip_active": "linear-gradient(135deg, #3b82f6, #1d4ed8)",
    },
    "cybersecurity": {
        "gradient": "linear-gradient(-45deg, #050a05, #0a1a0a, #0d200d, #0a180a, #030803)",
        "accent": "#00ff41",
        "glow": "rgba(0, 255, 65, 0.3)",
        "particle1": "rgba(0, 255, 65, 0.12)",
        "particle2": "rgba(0, 200, 50, 0.1)",
        "particle3": "rgba(0, 150, 40, 0.08)",
        "star_color": "#00ff41, #00cc33",
        "btn_gradient": "linear-gradient(135deg, #00cc33, #006622)",
        "chip_active": "linear-gradient(135deg, #00cc33, #006622)",
    },
}


def get_current_theme(sid: str):
    """Get the theme for the currently selected domain."""
    state = SESSION_STATES.get(sid)
    if not state or state["selected_domain"].value is None:
        return DOMAIN_THEMES["default"]
    name = state["selected_domain"].value.get("name", "").lower()
    return DOMAIN_THEMES.get(name, DOMAIN_THEMES["default"])


@solara.component
def MemberRow(sid: str, member: dict):
    cat   = member.get("category", "?")
    color = CATEGORY_COLOR.get(cat.lower(), "#cbd5e1")
    with solara.v.Html(
        tag="div",
        attributes={"class": "member-row"},
        style_="display:flex; justify-content:space-between; align-items:center; padding:14px 18px; border-bottom:1px solid rgba(56, 189, 248, 0.08);",
    ):
        with solara.v.Html(tag="div", style_="display:flex; align-items:center; gap:16px;"):
            solara.Text(member["name"], style={"font-weight": "600", "font-size": "15px", "color": "#e2e8f0"})
            solara.Text(
                cat,
                style={
                    "font-size": "11px", "padding": "4px 10px", "border-radius": "12px",
                    "background": f"rgba(56, 189, 248, 0.1)", "color": color, "font-weight": "700",
                    "text-transform": "uppercase", "letter-spacing": "0.5px"
                },
            )
        solara.Button(
            "✕",
            on_click=lambda: delete_member(sid, member["id"], member["name"]),
            small=True,
            icon=True,
            color="error",
            style="min-width:32px; height:32px; border-radius:50%; background:rgba(239, 68, 68, 0.1); border:1px solid rgba(239, 68, 68, 0.25); transition:all 0.2s ease;",
        )


@solara.component
def DomainSection(sid: str, domain_name: str, members: list, is_unassigned: bool = False):
    total = len(members)
    header_color = "#94a3b8" if is_unassigned else "#38bdf8"
    icon = "📋" if is_unassigned else "🏷️"
    with solara.v.Html(
        tag="div",
        attributes={"class": "domain-section"},
        style_=(
            "margin-bottom:24px; padding:24px; border-radius:16px;"
            "background:rgba(15, 23, 42, 0.6); backdrop-filter:blur(16px);"
            "border:1px solid rgba(56, 189, 248, 0.15); box-shadow:0 8px 32px rgba(56, 189, 248, 0.06);"
        )
    ):
        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; border-bottom:1px solid rgba(56, 189, 248, 0.1); padding-bottom:12px;"):
            solara.Text(
                f"{icon} {domain_name}",
                style={"font-weight": "800", "font-size": "18px", "color": header_color, "letter-spacing": "0.5px"},
            )
            solara.Text(
                f"{total} member{'s' if total != 1 else ''}",
                style={"font-size": "13px", "color": "rgba(255,255,255,0.6)", "font-weight": "600"},
            )
        if not members:
            solara.Text("No members in this domain.", style={"color": "rgba(255,255,255,0.5)", "font-size": "14px", "font-style": "italic"})
        else:
            for m in members:
                MemberRow(sid, m)


@solara.component
def DomainChips(sid: str):
    """Domain filter chips at the top."""
    theme = get_current_theme(sid)
    state = SESSION_STATES.get(sid)
    if not state: return

    accent = theme["accent"]
    chip_active = theme["chip_active"]
    glow = theme["glow"]
    
    with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:12px; margin-bottom:32px;"):
        # "All" chip
        all_active = state["selected_domain"].value is None
        solara.Button(
            "🌐 All Domains",
            on_click=lambda: clear_domain(sid),
            color="primary" if all_active else "default",
            small=True,
            outlined=not all_active,
            style=f"border-radius:20px; font-weight:700; {'background:' + chip_active + '; border:none; color:#fff; box-shadow:0 4px 15px ' + glow + ';' if all_active else 'background:' + accent + '14; color:#94a3b8; border:1px solid ' + accent + '33;'}"
        )
        for d in state["domains"].value:
            is_active = (
                state["selected_domain"].value is not None
                and state["selected_domain"].value["id"] == d["id"]
            )
            solara.Button(
                d["name"],
                on_click=lambda dom=d: select_domain(sid, dom),
                color="primary" if is_active else "default",
                small=True,
                outlined=not is_active,
                style=f"border-radius:20px; font-weight:700; {'background:' + chip_active + '; border:none; color:#fff; box-shadow:0 4px 15px ' + glow + ';' if is_active else 'background:' + accent + '14; color:#94a3b8; border:1px solid ' + accent + '33;'}"
            )


# ── Terminal Login ─────────────────────────────────────────────────

@solara.component
def TerminalLogin(sid: str):
    state = SESSION_STATES.get(sid)
    if not state: return
    
    terminal_password = state["terminal_password"]
    is_authorized = state["is_authorized"]
    terminal_error = state["terminal_error"]

    def submit():
        if terminal_password.value == "admin":  # Default password
            is_authorized.set(True)
        else:
            terminal_error.set(f"bash: {terminal_password.value or 'empty'}: permission denied")
            terminal_password.set("")

    solara.HTML(tag="style", unsafe_innerHTML="""
        .terminal-container {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            display: flex; justify-content: center; align-items: center;
            background-color: #030812; font-family: 'Courier New', Courier, monospace;
            z-index: 9999;
        }
        .terminal-window {
            width: 600px; background-color: rgba(10, 15, 20, 0.95);
            border: 1px solid #33ffdb; border-radius: 8px;
            box-shadow: 0 0 20px rgba(0, 255, 204, 0.2); overflow: hidden;
            backdrop-filter: blur(10px);
        }
        .terminal-header {
            background-color: #1a202c; padding: 10px 16px;
            display: flex; gap: 8px; align-items: center;
            border-bottom: 1px solid #2d3748;
        }
        .term-dot { width: 12px; height: 12px; border-radius: 50%; }
        .term-dot.red { background-color: #ff5f56; }
        .term-dot.yellow { background-color: #ffbd2e; }
        .term-dot.green { background-color: #27c93f; }
        .terminal-body { padding: 24px; color: #00ffcc; font-size: 15px; line-height: 1.6; }
        .term-input-row { display: flex; align-items: center; gap: 10px; margin-top: 20px; }
        .term-input {
            background: transparent !important; border: none !important;
            color: #00ffcc !important; font-family: 'Courier New', Courier, monospace !important;
            flex-grow: 1; outline: none; border-bottom: 1px solid #00ffcc !important; margin: 0;
            padding: 0;
        }
        .term-input .v-input__slot { background: transparent !important; box-shadow: none !important; }
        .term-input input { color: #00ffcc !important; font-family: 'Courier New', Courier, monospace !important; }
        .term-btn {
            background-color: #00ffcc !important; color: #000 !important; border: none !important; 
            padding: 8px 24px !important; margin-top: 30px !important;
            font-family: 'Courier New', Courier, monospace !important; font-weight: bold !important; 
            cursor: pointer !important; border-radius: 4px !important; transition: all 0.2s !important;
        }
        .term-btn:hover { background-color: #33ffdb !important; box-shadow: 0 0 10px rgba(51, 255, 219, 0.5) !important; }
    """)

    with solara.v.Html(tag="div", class_="terminal-container"):
        with solara.v.Html(tag="div", class_="terminal-window"):
            with solara.v.Html(tag="div", class_="terminal-header"):
                solara.v.Html(tag="div", class_="term-dot red")
                solara.v.Html(tag="div", class_="term-dot yellow")
                solara.v.Html(tag="div", class_="term-dot green")
                solara.Text("admin@group_maker: ~", style={"color": "#a0aec0", "font-size": "14px", "margin-left": "10px"})
            
            with solara.v.Html(tag="div", class_="terminal-body"):
                solara.Text("Group Maker Secure Portal", style={"display": "block", "font-weight": "bold", "margin-bottom": "8px"})
                solara.Text("System Locked. Authentication required.", style={"display": "block"})
                
                with solara.v.Html(tag="div", class_="term-input-row"):
                    solara.Text("password:", style={"color": "#00ffcc", "font-weight": "bold"})
                    solara.InputText("", value=terminal_password, password=True, classes=["term-input"])
                
                solara.Button("AUTHENTICATE", on_click=submit, classes=["term-btn"])
                if terminal_error.value:
                    solara.Text(terminal_error.value, style={"color": "#ff5f56", "display": "block", "margin-top": "16px"})


# Main Page

@solara.component
def Page():
    solara.Title("Members")
    sid = solara.get_session_id()
    state = get_session_state()

    is_authorized = state["is_authorized"]
    name_input = state["name_input"]
    category_input = state["category_input"]
    new_member_domains = state["new_member_domains"]
    status_msg = state["status_msg"]
    loading = state["loading"]
    domains = state["domains"]
    selected_domain = state["selected_domain"]
    members_in_domain = state["members_in_domain"]
    all_by_domain = state["all_by_domain"]

    if not is_authorized.value:
        TerminalLogin(sid)
    else:
        # Premium dark theme CSS
        solara.HTML(tag="style", unsafe_innerHTML="""
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
            html { scroll-behavior: smooth !important; }
            ::-webkit-scrollbar { width: 8px; }
            ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.8); }
            ::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #0ea5e9, #6366f1); border-radius: 10px; }
            ::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, #38bdf8, #818cf8); }
            .v-application, .v-application--wrap, .v-main, .v-main__wrap, .v-sheet { background-color: #030812 !important; background: #030812 !important; }
            .theme--light.v-sheet {{ background-color: #030812 !important; }}
            body { background-color: #0a0e1a !important; margin: 0; min-height: 100vh; }
            @keyframes gradientMembers { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
            @keyframes float-particle { 0%, 100% { transform: translateY(0) translateX(0) scale(1); opacity: 0.3; } 50% { transform: translateY(-30px) translateX(-20px) scale(0.85); opacity: 0.4; } }
            @keyframes shooting-star { 0% { transform: translateX(-100px) translateY(100px) rotate(-45deg); opacity: 0; } 30% { transform: translateX(calc(100vw + 200px)) translateY(-100vh) rotate(-45deg); opacity: 0; } }
            @keyframes btn-glow-pulse { 0%, 100% { box-shadow: 0 0 15px rgba(14, 165, 233, 0.3); } 50% { box-shadow: 0 0 25px rgba(14, 165, 233, 0.5); } }
            @keyframes fadeSlideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
            .members-bg-particle { position: absolute; border-radius: 50%; pointer-events: none; }
            .members-bg-particle:nth-child(1) { width: 350px; height: 350px; top: 5%; left: -8%; animation: float-particle 12s infinite; }
            .shooting-star { position: absolute; width: 120px; height: 2px; border-radius: 2px; pointer-events: none; opacity: 0; }
            .grid-overlay { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; }
            .v-btn { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important; position: relative !important; overflow: hidden !important; }
            .v-btn:hover { transform: translateY(-2px) scale(1.03) !important; filter: brightness(1.15) !important; }
            .add-member-btn { animation: btn-glow-pulse 3s infinite !important; }
            .glass-card { animation: fadeSlideUp 0.6s ease-out both; transition: all 0.4s !important; }
            .member-row { transition: all 0.3s ease !important; cursor: default; }
            .domain-section { animation: fadeSlideUp 0.5s ease-out both; transition: all 0.4s ease !important; }
            .v-text-field input { color: #00f0ff !important; text-shadow: 0 0 8px rgba(0, 240, 255, 0.4); font-weight: 600; }
        """)

        theme = get_current_theme(sid)
        accent, glow, bg_gradient, btn_grad = theme["accent"], theme["glow"], theme["gradient"], theme["btn_gradient"]

        solara.HTML(tag="style", unsafe_innerHTML=f"""
            .members-bg-particle:nth-child(1) {{ background: radial-gradient(circle, {theme['particle1']} 0%, transparent 70%); }}
            .shooting-star {{ background: linear-gradient(90deg, transparent, {theme['star_color']}, transparent); }}
            .add-member-btn {{ background: {btn_grad} !important; }}
            .v-btn:hover {{ box-shadow: 0 0 20px {accent}40 !important; }}
            ::-webkit-scrollbar-thumb {{ background: linear-gradient(180deg, {accent}, {accent}80) !important; }}
        """)

        def on_mount():
            fetch_domains(sid)
            fetch_all_by_domain(sid)
        solara.use_effect(on_mount, [])

        with solara.v.Html(tag="div", style_=f"min-height:100vh; position:relative; overflow:hidden; background:{bg_gradient}; background-size:400% 400%; animation:gradientMembers 20s ease infinite; color:#e2e8f0; padding-bottom:60px; box-sizing:border-box;"):
            for _ in range(3): solara.v.Html(tag="div", attributes={"class": "members-bg-particle"})
            solara.v.Html(tag="div", attributes={"class": "shooting-star"})
            with solara.v.Html(tag="div", style_="max-width:860px; margin:40px auto; padding:0 24px; position:relative; z-index:1;"):
                solara.v.Html(tag="div", children=["👥 Team Members"], style=f"font-size:36px; font-weight:900; color:#f1f5f9; margin-bottom:32px; text-shadow:0 2px 20px {glow};")
                DomainChips(sid)
                with solara.v.Html(tag="div", style_=f"background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px); border:1px solid {accent}33; border-radius:20px; padding:32px; margin-bottom:40px;"):
                    solara.Text("➕ Add New Member", style={"font-size":"22px", "font-weight":"800", "color":accent, "margin-bottom":"24px", "display":"block"})
                    with solara.v.Html(tag="div", style_="display:flex; gap:20px; flex-wrap:wrap; margin-bottom:20px;"):
                        solara.InputText("Name", value=name_input, style="flex:1; min-width:250px;")
                        solara.InputText("Category", value=category_input, style="flex:1; min-width:250px;")
                    if domains.value:
                        solara.Text("Assign to Domain(s):", style={"font-weight":"700", "font-size":"14px", "color":"rgba(255,255,255,0.7)", "margin-bottom":"12px", "display":"block"})
                        with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:24px;"):
                            for d in domains.value:
                                is_sel = d["id"] in new_member_domains.value
                                def toggle(dom=d):
                                    cur = list(new_member_domains.value)
                                    if dom["id"] in cur: cur.remove(dom["id"])
                                    else: cur.append(dom["id"])
                                    new_member_domains.set(cur)
                                solara.Button(("✓ " if is_sel else "") + d["name"], on_click=toggle, color="primary" if is_sel else "default", style=f"border-radius:12px; font-weight:600; {'background:'+btn_grad+';' if is_sel else ''}")
                    solara.Button("➕ Add Member", color="primary", on_click=lambda: add_member(sid), disabled=loading.value, style=f"width:100%; padding:14px; font-weight:800; border-radius:12px; background:{btn_grad}; color:#fff;")
                    if status_msg.value:
                        solara.Text(status_msg.value, style={"margin-top":"20px", "display":"block", "color": "#10b981" if '✅' in status_msg.value else "#ef4444"})
                with solara.v.Html(tag="div", style_=f"display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:24px; border-bottom:2px solid {accent}1a; padding-bottom:16px;"):
                    solara.Text(f"Members ({len(members_in_domain.value) if selected_domain.value else 'All'})", style={"font-size":"24px","font-weight":"800","color":accent})
                    solara.Button("🔄 Refresh", on_click=lambda: refresh(sid), outlined=True, small=True)
                if loading.value:
                    solara.Text("⚡ Loading...", style={"text-align":"center","display":"block","margin-top":"40px"})
                elif selected_domain.value:
                    for m in members_in_domain.value: MemberRow(sid, m)
                else:
                    for d_data in all_by_domain.value: DomainSection(sid, d_data["domain_name"], d_data["members"], is_unassigned=d_data.get("domain_id") is None)

