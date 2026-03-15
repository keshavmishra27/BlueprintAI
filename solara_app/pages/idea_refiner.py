import solara
import threading
import requests
import os
from pathlib import Path
from solara_app.components import CountdownTerminal

API = os.getenv("API_URL", "http://localhost:8000")

# ── Session State ──────────────────────────────────────────────────

SESSION_STATES = {}

def get_session_state():
    sid = solara.get_session_id()
    if sid not in SESSION_STATES:
        SESSION_STATES[sid] = {
            "user_idea": solara.reactive(""),
            "loading": solara.reactive(False),
            "error_msg": solara.reactive(""),
            "similar_projects": solara.reactive([]),
            "refinement": solara.reactive(None),
            "screen": solara.reactive("input"), # "input" or "results"
            "initialized": solara.reactive(False),
        }
    return SESSION_STATES[sid]

# ── Backend Calls ──────────────────────────────────────────────────

def _call_check_idea(sid: str):
    state = SESSION_STATES.get(sid)
    if not state: return
    
    idea = state["user_idea"].value
    try:
        r = requests.post(f"{API}/idea-validator/check", json={"idea": idea}, timeout=60)
        if r.status_code == 200:
            data = r.json()
            state["similar_projects"].set(data.get("similar_projects", []))
            state["screen"].set("results")
        else:
            state["error_msg"].set(f"Error: {r.text}")
    except Exception as e:
        state["error_msg"].set(f"Connection failed: {e}")
    finally:
        state["loading"].set(False)

def _call_refine_idea(sid: str):
    state = SESSION_STATES.get(sid)
    if not state: return
    
    idea = state["user_idea"].value
    try:
        r = requests.post(f"{API}/idea-validator/refine", json={"idea": idea}, timeout=90)
        if r.status_code == 200:
            data = r.json()
            state["refinement"].set(data)
            # Refine also ensures similar projects are fetched for context
            # Let's assume the backend did that or we can call check separately.
            # In our router, /refine calls check_similar_ideas internally, but it doesn't return them.
            # Wait, let's check the router. refine_idea doesn't return similar_projects.
            # I should update the router or just call check first.
            state["screen"].set("results")
        else:
            state["error_msg"].set(f"Error: {r.text}")
    except Exception as e:
        state["error_msg"].set(f"Connection failed: {e}")
    finally:
        state["loading"].set(False)

# ── Components ─────────────────────────────────────────────────────

@solara.component
def ProjectCard(project):
    with solara.v.Html(tag="div", style_="margin-bottom:20px; padding:20px; border-radius:16px; background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.05);"):
        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;"):
            with solara.v.Html(tag="div"):
                solara.Text(project.get("name", "Unknown Project"), style={"font-weight":"800", "color":"#00ffcc", "font-size":"18px", "display":"block"})
                if project.get("type"):
                    solara.Text(project["type"].upper(), style={"font-size":"10px", "font-weight":"900", "color":"rgba(255,255,255,0.4)", "letter-spacing":"1px"})
            
            if project.get("relevance_score"):
                with solara.v.Html(tag="div", style_="padding:4px 12px; border-radius:20px; background:rgba(0,255,204,0.1); border:1px solid #00ffcc;"):
                    solara.Text(f"{project['relevance_score']}% Match", style={"font-size":"12px", "font-weight":"800", "color":"#00ffcc"})

        solara.Text(project.get("overview", ""), style={"font-size":"14px", "color":"#cbd5e1", "display":"block", "margin-bottom":"12px", "line-height":"1.6"})
        
        if project.get("evidence"):
            solara.Text("EVIDENCE:", style={"font-size":"10px", "font-weight":"900", "color":"#94a3b8", "display":"block", "margin-bottom":"4px"})
            for ev in project["evidence"]:
                with solara.v.Html(tag="div", style_="margin-bottom:8px; padding-left:12px; border-left:2px solid rgba(255,255,255,0.1);"):
                    solara.Text(f'"{ev.get("quote","")}"', style={"font-size":"12px", "color":"#94a3b8", "font-style":"italic"})
                    if ev.get("source_url"):
                        solara.v.Html(tag="a", attributes={"href": ev["source_url"], "target": "_blank"}, children=[
                            solara.Text(f"Source ({ev.get('date', 'N/A')})", style={"font-size":"11px", "color":"#38bdf8", "display":"block", "margin-top":"2px", "text-decoration":"underline"})
                        ])

        with solara.v.Html(tag="div", style_="padding:10px; background:rgba(0,255,204,0.05); border-radius:8px; border-left:3px solid #00ffcc; margin-top:12px;"):
            solara.Text("V/S YOUR IDEA:", style={"font-size":"11px", "font-weight":"900", "color":"#00ffcc", "display":"block", "margin-bottom":"4px"})
            solara.Text(project.get("comparison", ""), style={"font-size":"13px", "color":"#94a3b8", "font-style":"italic"})
        
        if project.get("license_or_ip"):
            solara.Text(f"IP/License: {project['license_or_ip']}", style={"font-size":"11px", "color":"rgba(255,255,255,0.3)", "margin-top":"8px", "display":"block"})

@solara.component
def RefinementView(ref):
    if not ref: return
    with solara.v.Html(tag="div", style_="margin-top:24px;"):
        # Uniqueness
        uniq = ref.get("uniqueness", {})
        if isinstance(uniq, str): # Fallback for old schema
            uniq = {"verdict": "Unknown", "score": "?", "rationale": uniq}
        
        with solara.v.Html(tag="div", style_="padding:24px; border-radius:16px; background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.2); margin-bottom:24px; text-align:center;"):
            solara.Text(f"💎 Uniqueness: {uniq.get('verdict','').replace('_', ' ').title()}", style={"font-size":"12px", "color":"#818cf8", "letter-spacing":"2px", "display":"block", "margin-bottom":"8px"})
            solara.Text(f"{uniq.get('score', '')}% Novelty Score", style={"font-size":"20px", "font-weight":"800", "color":"#ffffff", "display":"block", "margin-bottom":"8px"})
            solara.Text(uniq.get("rationale",""), style={"font-size":"14px", "color":"#cbd5e1", "line-height":"1.6"})

        # Refined Concept
        concept = ref.get("refined_concept", {})
        if isinstance(concept, str):
            concept = {"final_direction": concept}
            
        with solara.v.Html(tag="div", style_="padding:24px; border-radius:16px; background:rgba(0,255,204,0.1); border:1px solid rgba(0,255,204,0.2); margin-bottom:32px;"):
            solara.Text("✨ Recommended Direction", style={"font-size":"18px", "font-weight":"800", "color":"#00ffcc", "display":"block", "margin-bottom":"12px"})
            solara.Text(concept.get("final_direction",""), style={"font-size":"16px", "line-height":"1.7", "color":"#e2e8f0", "font-weight":"700", "display":"block", "margin-bottom":"16px"})
            
            if concept.get("quick_win_variant"):
                with solara.v.Html(tag="div", style_="margin-bottom:12px; padding:12px; border-radius:8px; background:rgba(255,255,255,0.05);"):
                    solara.Text("🚀 Quick Win Variant", style={"font-size":"12px", "font-weight":"900", "color":"#38bdf8", "display":"block", "margin-bottom":"4px"})
                    solara.Text(concept["quick_win_variant"].get("description",""), style={"font-size":"13px", "color":"#cbd5e1"})

            if concept.get("high_diff_variant"):
                with solara.v.Html(tag="div", style_="padding:12px; border-radius:8px; background:rgba(0,255,204,0.05);"):
                    solara.Text("🏆 High Differentiation Variant", style={"font-size":"12px", "font-weight":"900", "color":"#00ffcc", "display":"block", "margin-bottom":"4px"})
                    solara.Text(concept["high_diff_variant"].get("description",""), style={"font-size":"13px", "color":"#cbd5e1"})

        # Patentability Assessment
        pa = ref.get("patentability_assessment")
        if pa:
            with solara.v.Html(tag="div", style_="padding:24px; border-radius:16px; background:rgba(244,63,94,0.05); border:1px solid rgba(244,63,94,0.2); margin-bottom:32px;"):
                solara.Text("🛡️ Patentability Triage", style={"font-size":"18px", "font-weight":"800", "color":"#f43f5e", "display":"block", "margin-bottom":"16px"})
                with solara.v.Html(tag="div", style_="display:flex; gap:16px; flex-wrap:wrap;"):
                    for key, label in [("novelty_summary", "Novelty"), ("inventive_step_summary", "Inventive Step"), ("industrial_applicability", "Industrial Applicability")]:
                        with solara.v.Html(tag="div", style_="flex:1; min-width:150px;"):
                            solara.Text(label, style={"font-size":"11px", "font-weight":"900", "color":"#fca5a5", "display":"block"})
                            solara.Text(pa.get(key,""), style={"font-size":"13px", "color":"#ffffff"})
                
                if pa.get("blocking_prior_art"):
                    solara.Text("Potential Blocks:", style={"font-size":"11px", "font-weight":"900", "color":"#fca5a5", "display":"block", "margin-top":"16px", "margin-bottom":"4px"})
                    for art in pa["blocking_prior_art"]:
                        solara.Text(f"• {art.get('patent_id', 'N/A')}: {art.get('summary','')}", style={"font-size":"12px", "color":"#ffffff"})

        # Novel Modifications
        mods = ref.get("recommended_novel_modifications")
        if mods:
            solara.Text("⚡ Technical Claims to Build", style={"font-size":"20px", "font-weight":"800", "color":"#f59e0b", "display":"block", "margin-bottom":"20px"})
            for mod in mods:
                with solara.v.Html(tag="div", style_="margin-bottom:20px; padding:20px; border-radius:12px; background:rgba(245,158,11,0.05); border-left:5px solid #f59e0b;"):
                    solara.Text(mod.get("short_title",""), style={"font-size":"16px", "font-weight":"800", "color":"#ffffff", "display":"block", "margin-bottom":"8px"})
                    solara.Text(mod.get("technical_description",""), style={"font-size":"14px", "color":"#cbd5e1", "margin-bottom":"12px", "display":"block"})
                    
                    with solara.v.Html(tag="div", style_="margin-top:12px; padding:10px; background:rgba(0,0,0,0.2); border-radius:6px;"):
                        solara.Text("LEGAL CLAIM DRAFT:", style={"font-size":"10px", "font-weight":"900", "color":"#94a3b8", "display":"block"})
                        solara.Text(mod.get("potential_claims_legal_style", [""])[0] if isinstance(mod.get("potential_claims_legal_style"), list) else mod.get("potential_claims_legal_style",""), style={"font-size":"12px", "color":"#ffffff", "font-family":"monospace"})

        # Loopholes
        loops = ref.get("loopholes")
        if loops:
            solara.Text("🔍 Strategic Gaps Identified", style={"font-size":"20px", "font-weight":"800", "color":"#0ea5e9", "display":"block", "margin-bottom":"20px", "margin-top":"32px"})
            for loop in loops:
                with solara.v.Html(tag="div", style_="margin-bottom:16px; padding:20px; border-radius:12px; background:rgba(14,165,233,0.05); border-left:5px solid #0ea5e9;"):
                    solara.Text(loop.get("issue",""), style={"font-size":"15px", "font-weight":"800", "color":"#ffffff", "display":"block", "margin-bottom":"8px"})
                    solara.Text(loop.get("description",""), style={"font-size":"14px", "color":"#cbd5e1", "margin-bottom":"12px", "display":"block"})
                    
                    sol = loop.get("proposed_solution", {})
                    if isinstance(sol, str): sol = {"short": sol}
                    
                    with solara.v.Html(tag="div", style_="padding:12px; background:rgba(16,185,129,0.05); border-radius:8px; border-left:3px solid #10b981;"):
                        solara.Text("THE FIX:", style={"font-size":"11px", "font-weight":"900", "color":"#10b981", "display":"block", "margin-bottom":"4px"})
                        solara.Text(sol.get("short",""), style={"font-size":"14px", "color":"#ffffff", "font-weight":"700", "display":"block"})
                        solara.Text(sol.get("technical_details",""), style={"font-size":"13px", "color":"#d1fae5"})
                        if sol.get("dev_effort_hours"):
                            solara.Text(f"Estimated Effort: {sol['dev_effort_hours']} hrs", style={"font-size":"11px", "color":"#10b981", "margin-top":"8px", "display":"block"})

        # Implementation Plan
        plan = ref.get("implementation_plan_high_level")
        if plan:
            with solara.v.Html(tag="div", style_="margin-top:32px; padding:24px; border-radius:16px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05);"):
                solara.Text("🏗️ Implementation Roadmap", style={"font-size":"18px", "font-weight":"800", "color":"#ffffff", "display":"block", "margin-bottom":"16px"})
                for ms in plan.get("milestones", []):
                    with solara.v.Html(tag="div", style_="display:flex; gap:16px; margin-bottom:12px;"):
                        solara.Text(f"{ms.get('duration_days', '?')}d", style={"font-size":"12px", "font-weight":"900", "color":"#94a3b8", "padding-top":"4px"})
                        with solara.v.Html(tag="div"):
                            solara.Text(ms.get("name",""), style={"font-size":"14px", "font-weight":"700", "color":"#ffffff"})
                            solara.Text(", ".join(ms.get("tasks", [])), style={"font-size":"12px", "color":"#94a3b8"})


@solara.component
def Page():
    solara.Title("Idea Refiner")
    state = get_session_state()
    
    # ── Inject Styling ──────────────────────────────────────────────
    solara.HTML(tag="style", unsafe_innerHTML="""
        .v-application, .v-application--wrap, .v-main, .v-main__wrap, .v-sheet {
            background-color: #030812 !important;
            background: #030812 !important;
        }
        body { background-color: #030812 !important; margin: 0; }
        .v-text-field > .v-input__control > .v-input__slot {
            background: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
        }
        .v-text-field input, .v-textarea textarea { color: #00f0ff !important; font-weight: 600 !important; }
        .v-label { color: rgba(255, 255, 255, 0.5) !important; }
    """)

    def start_init():
        if not state["initialized"].value:
            def wait_anim():
                import time
                time.sleep(3.5) # Hacker intro
                state["initialized"].set(True)
            threading.Thread(target=wait_anim, daemon=True).start()
    
    solara.use_effect(start_init, [])

    if not state["initialized"].value:
        CountdownTerminal()
        return

    with solara.v.Html(tag="div", style_="max-width:860px; margin:40px auto; padding:0 24px; min-height:100vh;"):
        
            def on_check():
                if not state["user_idea"].value.strip():
                    state["error_msg"].set("Please describe your idea first.")
                    return
                state["loading"].set(True)
                state["error_msg"].set("")
                threading.Thread(target=_call_check_idea, args=(solara.get_session_id(),), daemon=True).start()
            
            def on_refine():
                if not state["user_idea"].value.strip():
                    state["error_msg"].set("Please describe your idea first.")
                    return
                state["loading"].set(True)
                state["error_msg"].set("")
                threading.Thread(target=_call_refine_idea, args=(solara.get_session_id(),), daemon=True).start()

            if state["screen"].value == "input":
                # ── Header ──────────────────────────────────────────────
                solara.Text("💡 Idea Validator & Refiner", style={"font-size":"36px", "font-weight":"900", "color":"#ffffff", "display":"block", "margin-bottom":"12px", "text-shadow":"0 0 20px rgba(99,102,241,0.5)"})
                solara.Text("Enter your project idea. We'll check if it already exists and help you find a unique angle with market loophole analysis.", style={"font-size":"16px", "color":"rgba(255,255,255,0.7)", "margin-bottom":"40px", "display":"block"})

                # ── Form ────────────────────────────────────────────────
                with solara.v.Html(tag="div", style_="width:100%; margin-bottom:24px;"):
                    solara.InputTextArea(
                        label="Describe your project idea in detail...",
                        value=state["user_idea"].value,
                        on_value=state["user_idea"].set,
                        rows=5,
                        continuous_update=True,
                    )

                if state["error_msg"].value:
                    solara.Text(state["error_msg"].value, style={"color":"#ef4444", "margin-bottom":"16px", "display":"block"})

                solara.Button(
                    "🔍 Check Similarities" if not state["loading"].value else "⏳ Searching...",
                    on_click=on_check,
                    disabled=state["loading"].value,
                    style="width:100%; padding:20px; font-weight:800; border-radius:12px; background:rgba(255,255,255,0.05); color:#ffffff; border:1px solid rgba(255,255,255,0.1);"
                )
            else:
                # ── Results Screen ──────────────────────────────────────
                with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:32px;"):
                    solara.Text("📊 Analysis Results", style={"font-size":"28px", "font-weight":"900", "color":"#ffffff"})
                    solara.Button("← Start Over", on_click=lambda: state["screen"].set("input"), style="background:transparent; color:#818cf8; text-transform:none;")

                with solara.v.Html(tag="div", style_="margin-bottom:40px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:32px;"):
                    solara.Text("YOUR IDEA:", style={"font-size":"11px", "letter-spacing":"1px", "color":"rgba(255,255,255,0.4)", "display":"block", "margin-bottom":"8px"})
                    solara.Text(state["user_idea"].value, style={"font-size":"16px", "color":"#ffffff", "font-style":"italic", "line-height":"1.6"})

                # Refinement (if exists)
                if state["refinement"].value:
                    RefinementView(state["refinement"].value)

                # Similar Projects
                if state["similar_projects"].value:
                    solara.Text("🏢 Similar Existing Projects", style={"font-size":"20px", "font-weight":"800", "color":"#0ea5e9", "display":"block", "margin-bottom":"20px", "margin-top":"40px"})
                    for proj in state["similar_projects"].value:
                        ProjectCard(proj)
                elif not state["refinement"].value:
                    solara.Text("No similar projects found! Your idea might be very unique or too niche for the model's current knowledge.", style={"color":"#10b981", "font-style":"italic"})

                if not state["refinement"].value:
                    solara.Button(
                        "🚀 Refine & Find Gaps" if not state["loading"].value else "🧠 Analyzing...",
                        on_click=on_refine,
                        disabled=state["loading"].value,
                        style="width:100%; margin-top:40px; padding:20px; font-weight:800; border-radius:12px; background:linear-gradient(90deg, #6366f1, #00ffcc); color:#000;"
                    )

                solara.Button("Return to Input", on_click=lambda: state["screen"].set("input"), style="width:100%; margin-top:20px; padding:16px; border-radius:8px; background:rgba(255,255,255,0.1); color:#fff;")
