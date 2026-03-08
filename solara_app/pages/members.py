import solara
import requests
import os
from typing import List

API = os.getenv("API_URL", "http://localhost:8000")

# Reactive state
domains           = solara.reactive([])         # [{id, name}, ...]
selected_domain   = solara.reactive(None)       # None = all; or {id, name}

members_in_domain = solara.reactive([])         # when a domain is selected
all_by_domain     = solara.reactive([])         # [{domain_name, members:[...]}, ...]

# Add-member form
name_input        = solara.reactive("")
category_input    = solara.reactive("")
new_member_domains= solara.reactive([])    # list of domain IDs chosen for new member
status_msg        = solara.reactive("")
loading           = solara.reactive(False)

# Terminal Login state
is_authorized     = solara.reactive(False)
terminal_password = solara.reactive("")
terminal_error    = solara.reactive("")


# Data fetchers
def fetch_domains():
    try:
        r = requests.get(f"{API}/members/domains", timeout=5)
        domains.set(r.json())
    except Exception as e:
        status_msg.set(f"❌ Could not load domains: {e}")


def fetch_for_domain(domain_id: int):
    loading.set(True)
    try:
        r = requests.get(f"{API}/members/", params={"domain_id": domain_id}, timeout=5)
        members_in_domain.set(r.json())
    except Exception as e:
        status_msg.set(f"❌ {e}")
    finally:
        loading.set(False)


def fetch_all_by_domain():
    loading.set(True)
    try:
        r = requests.get(f"{API}/members/by-domain", timeout=5)
        all_by_domain.set(r.json())
    except Exception as e:
        status_msg.set(f"❌ {e}")
    finally:
        loading.set(False)


def refresh():
    """Re-fetch whatever view is currently active."""
    status_msg.set("")
    if selected_domain.value:
        fetch_for_domain(selected_domain.value["id"])
    else:
        fetch_all_by_domain()


def select_domain(domain):
    """Called when user clicks a domain chip."""
    selected_domain.set(domain)
    status_msg.set("")
    if domain:
        fetch_for_domain(domain["id"])


def clear_domain():
    selected_domain.set(None)
    fetch_all_by_domain()


def add_member():
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
            refresh()
        else:
            status_msg.set(f"❌ {r.json().get('detail', r.text)}")
    except Exception as e:
        status_msg.set(f"❌ {e}")
    finally:
        loading.set(False)


def delete_member(member_id: int, member_name: str):
    try:
        r = requests.delete(f"{API}/members/{member_id}", timeout=5)
        if r.status_code == 200:
            status_msg.set(f"🗑️ '{member_name}' deleted.")
            refresh()
        else:
            status_msg.set(f"❌ {r.text}")
    except Exception as e:
        status_msg.set(f"❌ {e}")


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


def get_current_theme():
    """Get the theme for the currently selected domain."""
    if selected_domain.value is None:
        return DOMAIN_THEMES["default"]
    name = selected_domain.value.get("name", "").lower()
    return DOMAIN_THEMES.get(name, DOMAIN_THEMES["default"])


@solara.component
def MemberRow(member: dict):
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
            on_click=lambda: delete_member(member["id"], member["name"]),
            small=True,
            icon=True,
            color="error",
            style="min-width:32px; height:32px; border-radius:50%; background:rgba(239, 68, 68, 0.1); border:1px solid rgba(239, 68, 68, 0.25); transition:all 0.2s ease;",
        )


@solara.component
def DomainSection(domain_name: str, members: list, is_unassigned: bool = False):
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
                MemberRow(m)


@solara.component
def DomainChips():
    """Domain filter chips at the top."""
    theme = get_current_theme()
    accent = theme["accent"]
    chip_active = theme["chip_active"]
    glow = theme["glow"]
    with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:12px; margin-bottom:32px;"):
        # "All" chip
        all_active = selected_domain.value is None
        solara.Button(
            "🌐 All Domains",
            on_click=clear_domain,
            color="primary" if all_active else "default",
            small=True,
            outlined=not all_active,
            style=f"border-radius:20px; font-weight:700; {'background:' + chip_active + '; border:none; color:#fff; box-shadow:0 4px 15px ' + glow + ';' if all_active else 'background:' + accent + '14; color:#94a3b8; border:1px solid ' + accent + '33;'}"
        )
        for d in domains.value:
            is_active = (
                selected_domain.value is not None
                and selected_domain.value["id"] == d["id"]
            )
            solara.Button(
                d["name"],
                on_click=lambda dom=d: select_domain(dom),
                color="primary" if is_active else "default",
                small=True,
                outlined=not is_active,
                style=f"border-radius:20px; font-weight:700; {'background:' + chip_active + '; border:none; color:#fff; box-shadow:0 4px 15px ' + glow + ';' if is_active else 'background:' + accent + '14; color:#94a3b8; border:1px solid ' + accent + '33;'}"
            )


# ── Terminal Login ─────────────────────────────────────────────────

@solara.component
def TerminalLogin():
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
        .terminal-body {
            padding: 24px; color: #00ffcc; font-size: 15px; line-height: 1.6;
        }
        .term-input-row { display: flex; align-items: center; gap: 10px; margin-top: 20px; }
        .term-input {
            background: transparent !important; border: none !important;
            color: #00ffcc !important; font-family: 'Courier New', Courier, monospace !important;
            flex-grow: 1; outline: none; border-bottom: 1px solid #00ffcc !important; margin: 0;
            padding: 0;
        }
        .term-input .v-input__slot {
            background: transparent !important; box-shadow: none !important;
        }
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
                    solara.InputText(
                        "", 
                        value=terminal_password, 
                        password=True, 
                        classes=["term-input"]
                    )
                
                solara.Button("AUTHENTICATE", on_click=submit, classes=["term-btn"])
                
                if terminal_error.value:
                    solara.Text(terminal_error.value, style={"color": "#ff5f56", "display": "block", "margin-top": "16px"})


# Main Page

@solara.component
def Page():
    solara.Title("Members")

    if not is_authorized.value:
        with solara.v.Html(tag="div"):
            TerminalLogin()
    else:
        with solara.v.Html(tag="div"):
            # Premium dark theme CSS with cool effects
            solara.HTML(tag="style", unsafe_innerHTML="""
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        /* === SMOOTH SCROLL === */
        html { scroll-behavior: smooth !important; }
        
        /* === CUSTOM SCROLLBAR === */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.8); }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #0ea5e9, #6366f1);
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, #38bdf8, #818cf8); }

        .v-application, .v-application--wrap, .v-main__wrap {
            background: transparent !important;
        }
        body {
            background-color: #0a0e1a !important;
            margin: 0;
            min-height: 100vh;
        }

        /* === KEYFRAMES === */
        @keyframes gradientMembers {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes float-particle {
            0%, 100% { transform: translateY(0) translateX(0) scale(1); opacity: 0.3; }
            25% { transform: translateY(-60px) translateX(30px) scale(1.2); opacity: 0.7; }
            50% { transform: translateY(-30px) translateX(-20px) scale(0.85); opacity: 0.4; }
            75% { transform: translateY(-80px) translateX(15px) scale(1.1); opacity: 0.6; }
        }
        @keyframes shooting-star {
            0% { transform: translateX(-100px) translateY(100px) rotate(-45deg); opacity: 0; }
            5% { opacity: 1; }
            15% { opacity: 1; }
            30% { transform: translateX(calc(100vw + 200px)) translateY(-100vh) rotate(-45deg); opacity: 0; }
            100% { opacity: 0; }
        }
        @keyframes grid-scroll {
            0% { transform: perspective(500px) rotateX(60deg) translateY(0); }
            100% { transform: perspective(500px) rotateX(60deg) translateY(50px); }
        }
        @keyframes pulse-ring {
            0% { transform: scale(1); opacity: 0.4; }
            100% { transform: scale(1.8); opacity: 0; }
        }
        @keyframes btn-glow-pulse {
            0%, 100% { box-shadow: 0 0 15px rgba(14, 165, 233, 0.3), 0 0 30px rgba(99, 102, 241, 0.15); }
            50% { box-shadow: 0 0 25px rgba(14, 165, 233, 0.5), 0 0 50px rgba(99, 102, 241, 0.3), 0 0 80px rgba(14, 165, 233, 0.1); }
        }
        @keyframes fadeSlideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes borderGlow {
            0%, 100% { border-color: rgba(56, 189, 248, 0.2); }
            50% { border-color: rgba(56, 189, 248, 0.5); }
        }

        /* === BACKGROUND PARTICLES === */
        .members-bg-particle {
            position: absolute;
            border-radius: 50%;
            pointer-events: none;
            filter: blur(1px);
        }
        .members-bg-particle:nth-child(1) {
            width: 350px; height: 350px; top: 5%; left: -8%;
            background: radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, transparent 70%);
            animation: float-particle 12s ease-in-out infinite;
        }
        .members-bg-particle:nth-child(2) {
            width: 280px; height: 280px; top: 45%; right: -10%;
            background: radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%);
            animation: float-particle 16s ease-in-out infinite 3s;
        }
        .members-bg-particle:nth-child(3) {
            width: 220px; height: 220px; bottom: 8%; left: 25%;
            background: radial-gradient(circle, rgba(20, 184, 166, 0.12) 0%, transparent 70%);
            animation: float-particle 14s ease-in-out infinite 6s;
        }
        .members-bg-particle:nth-child(4) {
            width: 200px; height: 200px; top: 20%; right: 15%;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
            animation: float-particle 18s ease-in-out infinite 2s;
        }

        /* === SHOOTING STARS === */
        .shooting-star {
            position: absolute;
            width: 120px; height: 2px;
            background: linear-gradient(90deg, transparent, #38bdf8, #6366f1, transparent);
            border-radius: 2px;
            pointer-events: none;
            opacity: 0;
        }
        .shooting-star:nth-child(5) {
            top: 15%; left: 0;
            animation: shooting-star 6s ease-in-out infinite 1s;
        }
        .shooting-star:nth-child(6) {
            top: 40%; left: 0;
            animation: shooting-star 8s ease-in-out infinite 3.5s;
        }
        .shooting-star:nth-child(7) {
            top: 70%; left: 0;
            animation: shooting-star 7s ease-in-out infinite 6s;
        }

        /* === GRID OVERLAY === */
        .grid-overlay {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            background-image:
                linear-gradient(rgba(56, 189, 248, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(56, 189, 248, 0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            mask-image: radial-gradient(ellipse at center, rgba(0,0,0,0.4) 0%, transparent 75%);
            -webkit-mask-image: radial-gradient(ellipse at center, rgba(0,0,0,0.4) 0%, transparent 75%);
        }

        /* === BUTTON EFFECTS === */
        .v-btn {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
            overflow: hidden !important;
        }
        .v-btn:hover {
            transform: translateY(-2px) scale(1.03) !important;
            filter: brightness(1.15) !important;
        }
        .v-btn:active {
            transform: translateY(0px) scale(0.98) !important;
        }
        /* Ripple glow on hover */
        .v-btn::after {
            content: '';
            position: absolute;
            top: 50%; left: 50%;
            width: 0; height: 0;
            border-radius: 50%;
            background: rgba(56, 189, 248, 0.15);
            transform: translate(-50%, -50%);
            transition: width 0.5s ease, height 0.5s ease;
        }
        .v-btn:hover::after {
            width: 300px; height: 300px;
        }

        /* === ADD MEMBER BUTTON GLOW === */
        .add-member-btn {
            animation: btn-glow-pulse 3s ease-in-out infinite !important;
        }
        .add-member-btn:hover {
            animation: none !important;
            box-shadow: 0 0 30px rgba(14, 165, 233, 0.6), 0 0 60px rgba(99, 102, 241, 0.3), 0 8px 25px rgba(0,0,0,0.4) !important;
            transform: translateY(-3px) scale(1.02) !important;
        }

        /* === CARD EFFECTS === */
        .glass-card {
            animation: fadeSlideUp 0.6s ease-out both, borderGlow 4s ease-in-out infinite;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        .glass-card:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 30px rgba(56, 189, 248, 0.1) !important;
            border-color: rgba(56, 189, 248, 0.4) !important;
        }

        /* === MEMBER ROW HOVER === */
        .member-row {
            transition: all 0.3s ease !important;
            cursor: default;
        }
        .member-row:hover {
            background: rgba(56, 189, 248, 0.06) !important;
            padding-left: 24px !important;
        }

        /* === DOMAIN SECTION HOVER === */
        .domain-section {
            animation: fadeSlideUp 0.5s ease-out both;
            transition: all 0.4s ease !important;
        }
        .domain-section:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.3), 0 0 20px rgba(56, 189, 248, 0.08) !important;
        }

        /* === CHIP HOVER EFFECTS === */
        .domain-chip {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        .domain-chip:hover {
            transform: translateY(-3px) scale(1.05) !important;
            box-shadow: 0 8px 25px rgba(14, 165, 233, 0.25) !important;
        }

        /* === TITLE EFFECTS === */
        .page-title {
            animation: fadeSlideUp 0.8s ease-out both;
        }

        /* === TYPING TEXT === */
        .v-text-field input, .v-textarea textarea, .v-input input {
            color: #00f0ff !important;
            text-shadow: 0 0 8px rgba(0, 240, 255, 0.4);
            font-weight: 600;
        }
        .v-text-field .v-label {
            color: rgba(255,255,255,0.6) !important;
        }

        /* === STATUS MSG === */
        .custom-status-msg {
            margin-top:20px;
            padding:12px 16px;
            border-radius:10px;
            font-weight:600;
            font-size:14px;
            color:#ffffff;
            animation: fadeSlideUp 0.4s ease-out both;
        }
        .custom-status-success {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .custom-status-error {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
    """)


    # --- Dynamic theme based on selected domain ---
    theme = get_current_theme()
    accent = theme["accent"]
    glow = theme["glow"]
    bg_gradient = theme["gradient"]
    btn_grad = theme["btn_gradient"]

    # Dynamic CSS injection that overrides accent colors per domain
    solara.HTML(tag="style", unsafe_innerHTML=f"""
        /* === DYNAMIC THEME OVERRIDES === */
        .members-bg-particle:nth-child(1) {{
            background: radial-gradient(circle, {theme['particle1']} 0%, transparent 70%) !important;
        }}
        .members-bg-particle:nth-child(2) {{
            background: radial-gradient(circle, {theme['particle2']} 0%, transparent 70%) !important;
        }}
        .members-bg-particle:nth-child(3) {{
            background: radial-gradient(circle, {theme['particle3']} 0%, transparent 70%) !important;
        }}
        .shooting-star {{
            background: linear-gradient(90deg, transparent, {theme['star_color']}, transparent) !important;
        }}
        .grid-overlay {{
            background-image:
                linear-gradient({accent}12 1px, transparent 1px),
                linear-gradient(90deg, {accent}12 1px, transparent 1px) !important;
        }}
        .add-member-btn {{
            background: {btn_grad} !important;
            animation: btn-glow-pulse 3s ease-in-out infinite !important;
        }}
        .add-member-btn:hover {{
            animation: none !important;
            box-shadow: 0 0 30px {glow}, 0 0 60px {glow}, 0 8px 25px rgba(0,0,0,0.4) !important;
            transform: translateY(-3px) scale(1.02) !important;
        }}
        @keyframes btn-glow-pulse {{
            0%, 100% {{ box-shadow: 0 0 15px {glow}, 0 0 30px {accent}20; }}
            50% {{ box-shadow: 0 0 25px {glow}, 0 0 50px {accent}30, 0 0 80px {accent}15; }}
        }}
        @keyframes borderGlow {{
            0%, 100% {{ border-color: {accent}33; }}
            50% {{ border-color: {accent}80; }}
        }}

        /* Enhanced button hover glow */
        .v-btn:hover {{
            transform: translateY(-2px) scale(1.04) !important;
            filter: brightness(1.2) !important;
            box-shadow: 0 0 20px {accent}40, 0 4px 15px rgba(0,0,0,0.3) !important;
        }}
        .v-btn:active {{
            transform: translateY(0px) scale(0.97) !important;
            box-shadow: 0 0 10px {accent}30 !important;
        }}
        .v-btn::after {{
            background: {accent}20 !important;
        }}

        /* Delete button enhanced glow */
        .v-btn.error--text:hover,
        .v-btn[color="error"]:hover {{
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.5), 0 0 40px rgba(239, 68, 68, 0.2) !important;
            background: rgba(239, 68, 68, 0.2) !important;
        }}

        .domain-chip:hover {{
            box-shadow: 0 8px 25px {accent}40 !important;
        }}

        .member-row:hover {{
            background: {accent}10 !important;
            box-shadow: inset 3px 0 0 {accent} !important;
        }}

        .domain-section:hover {{
            box-shadow: 0 16px 48px rgba(0,0,0,0.3), 0 0 25px {accent}15 !important;
            border-color: {accent}50 !important;
        }}

        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, {accent}, {accent}80) !important;
        }}
    """)

    def on_mount():
        fetch_domains()
        fetch_all_by_domain()

    solara.use_effect(on_mount, [])

    with solara.v.Html(
        tag="div",
        style_=(
            "min-height:100vh;"
            "position:relative; overflow:hidden;"
            f"background: {bg_gradient};"
            "background-size: 400% 400%;"
            "animation: gradientMembers 20s ease infinite;"
            "font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
            "color:#e2e8f0;"
            "padding-bottom:60px;"
            "box-sizing:border-box;"
            "transition: background 1s ease;"
        )
    ):
        # Floating background particles
        for _ in range(4):
            solara.v.Html(tag="div", attributes={"class": "members-bg-particle"})
        # Shooting stars
        for _ in range(3):
            solara.v.Html(tag="div", attributes={"class": "shooting-star"})
        # Grid overlay
        solara.v.Html(tag="div", attributes={"class": "grid-overlay"})
        with solara.v.Html(tag="div", style_="max-width:860px; margin:40px auto; padding:0 24px; position:relative; z-index:1;"):
            solara.v.Html(tag="div", attributes={"class": "page-title"}, children=["👥 Team Members"], style_=f"font-size:36px; font-weight:900; color:#f1f5f9; margin-bottom:32px; text-shadow:0 2px 20px {glow};")

            # Domain filter chips
            DomainChips()

            # Add Member Form
            with solara.v.Html(
                tag="div",
                attributes={"class": "glass-card"},
                style_=(
                    "background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(20px);"
                    f"border:1px solid {accent}33; border-radius:20px;"
                    "padding:32px; box-shadow:0 12px 40px rgba(0, 0, 0, 0.3);"
                    "margin-bottom:40px;"
                )
            ):
                solara.Text("➕ Add New Member", style={"font-size": "22px", "font-weight": "800", "color": accent, "margin-bottom": "24px", "display": "block"})
                
                with solara.v.Html(tag="div", style_="display:flex; gap:20px; flex-wrap:wrap; margin-bottom:20px;"):
                    with solara.v.Html(tag="div", style_="flex:1; min-width:250px;"):
                        solara.InputText("Name", value=name_input, style="width:100%;")
                    with solara.v.Html(tag="div", style_="flex:1; min-width:250px;"):
                        solara.InputText(
                            "Category (senior/intermediate/junior)",
                            value=category_input,
                            style="width:100%;",
                        )

                # Domain selection
                if domains.value:
                    solara.Text("Assign to Domain(s):", style={"font-weight": "700", "font-size": "14px", "color": "rgba(255,255,255,0.7)", "margin-bottom": "12px", "display": "block"})
                    with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:24px;"):
                        for d in domains.value:
                            is_sel = d["id"] in new_member_domains.value
                            def toggle(dom=d):
                                cur = list(new_member_domains.value)
                                if dom["id"] in cur:
                                    cur.remove(dom["id"])
                                else:
                                    cur.append(dom["id"])
                                new_member_domains.set(cur)
                            solara.Button(
                                ("✓ " if is_sel else "") + d["name"],
                                on_click=toggle,
                                color="primary" if is_sel else "default",
                                outlined=not is_sel,
                                small=True,
                                style=f"border-radius:12px; font-weight:600; {'background:' + btn_grad + '; border:none; color:#fff; box-shadow:0 2px 10px ' + glow + ';' if is_sel else 'background:' + accent + '14; color:#94a3b8; border:1px solid ' + accent + '33;'}"
                            )
                else:
                    solara.Text("No domains available yet.", style={"color": "rgba(255,255,255,0.5)", "font-size": "13px", "font-style": "italic", "display": "block"})

                solara.Button(
                    "➕ Add Member",
                    color="primary",
                    on_click=add_member,
                    disabled=loading.value,
                    attributes={"class": "add-member-btn"},
                    style=f"width:100%; padding:14px; font-weight:800; font-size:16px; letter-spacing:1px; border-radius:12px; background:{btn_grad}; border:none; color:#fff;",
                )

                if status_msg.value:
                    with solara.v.Html(
                        tag="div",
                        attributes={"class": "custom-status-msg " + ("custom-status-success" if '✅' in status_msg.value else "custom-status-error")},
                    ):
                        solara.Text(status_msg.value)

                # Refresh button
                with solara.v.Html(tag="div", style_=f"display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:24px; border-bottom:2px solid {accent}1a; padding-bottom:16px;"):
                    if selected_domain.value:
                        solara.Text(
                            f"Members of {selected_domain.value['name']} ({len(members_in_domain.value)})",
                            style={"font-size": "24px", "font-weight": "800", "color": accent, "display": "block"}
                        )
                    else:
                        total = sum(len(d["members"]) for d in all_by_domain.value)
                        solara.Text(f"All Members ({total} total)", style={"font-size": "24px", "font-weight": "800", "color": accent, "display": "block"})
                    
                    solara.Button("🔄 Refresh", on_click=refresh, outlined=True, small=True, style=f"background:{accent}14; color:{accent}; border:1px solid {accent}4d; border-radius:10px;")

                if loading.value:
                    solara.Text("⚡ Loading data...", style={"color": "rgba(255,255,255,0.7)", "font-size": "16px", "font-weight": "600", "text-align": "center", "display": "block", "margin-top": "40px"})
                    return

                # Single domain view
                if selected_domain.value:
                    if not members_in_domain.value:
                        with solara.v.Html(tag="div", style_=f"text-align:center; padding:40px; background:rgba(15, 23, 42, 0.5); border-radius:16px; border:1px dashed {accent}33;"):
                            solara.Text(
                                "No members in this domain yet.",
                                style={"color": "rgba(255,255,255,0.6)", "font-size": "16px", "font-style": "italic", "display": "block"},
                            )
                    else:
                        with solara.v.Html(tag="div", style_=f"background:rgba(15, 23, 42, 0.6); backdrop-filter:blur(16px); border:1px solid {accent}26; border-radius:16px; overflow:hidden;"):
                            for m in members_in_domain.value:
                                MemberRow(m)

                # All domains view
                else:
                    if not all_by_domain.value:
                        solara.Text(
                            "Loading members… if this persists, check your API connection.",
                            style={"color": "rgba(255,255,255,0.6)", "text-align": "center", "display": "block", "margin-top": "40px"},
                        )
                    else:
                        for domain_data in all_by_domain.value:
                            is_unassigned = domain_data.get("domain_id") is None
                            DomainSection(
                                domain_data["domain_name"],
                                domain_data["members"],
                                is_unassigned=is_unassigned,
                            )

