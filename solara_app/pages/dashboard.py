import solara
from solara_app.api_client import api_get
import json

@solara.component
def Page():
    solara.Title("BlueprintAI - Decisions Dashboard")
    
    decisions, set_decisions = solara.use_state([])
    error, set_error = solara.use_state(None)
    
    def fetch_decisions():
        try:
            res = api_get("/api/v1/decisions")
            res.raise_for_status()
            set_decisions(res.json())
            set_error(None)
        except Exception as e:
            set_error(str(e))
            set_decisions([])
            
    solara.use_effect(fetch_decisions, [])
    
    with solara.Column(margin=4):
        solara.Markdown("# BlueprintAI Decisions Dashboard")
        solara.Markdown("Governance and Architectural Decisions tracked by BlueprintAI.")
        
        solara.Button("Refresh Decisions", on_click=fetch_decisions, color="primary")
        
        if error:
            solara.Error(f"Failed to fetch decisions: {error}")
            
        if not decisions and not error:
            solara.Info("No decisions found or still loading.")
            
        for d in decisions:
            with solara.Card(title=f"Decision {d.get('id')}", elevation=2, margin=2):
                with solara.Columns([1, 1, 1]):
                    with solara.Column():
                        solara.Markdown("### Identity")
                        solara.Markdown(f"**Decision ID:** `{d.get('id')}`")
                        solara.Markdown(f"**Version:** `{d.get('version')}`")
                        solara.Markdown(f"**Decision Fingerprint:** `{d.get('decision_fingerprint')}`")
                        solara.Markdown(f"**Graph Fingerprint:** `{d.get('graph_fingerprint')}`")
                    
                    with solara.Column():
                        gov = d.get("governance", {})
                        action = gov.get("action", "UNKNOWN")
                        severity = gov.get("severity", "UNKNOWN")
                        
                        solara.Markdown("### Governance State")
                        
                        color = "info"
                        if action in ["REJECTED", "BLOCK"]: color = "error"
                        elif action in ["UNRESOLVED", "REVIEW"]: color = "warning"
                        elif action in ["APPROVE", "RECOMMEND", "PROCEED"]: color = "success"
                            
                        solara.Alert(f"Action: **{action}** (Severity: {severity})", color=color, dense=True)
                        
                        scores = gov.get("scores", {})
                        if scores:
                            solara.Markdown("**Epistemic Uncertainty / Scores:**")
                            for k, v in scores.items():
                                solara.Markdown(f"- {k}: {v}")
                        else:
                            solara.Markdown("*No additional epistemic metadata/scores recorded.*")
                            
                    with solara.Column():
                        arch = d.get("architecture", {})
                        components = arch.get("components", [])
                        
                        solara.Markdown("### Architecture & Components")
                        if components:
                            for comp in components:
                                solara.Markdown(f"- **{comp.get('name')}** ({comp.get('type')})")
                        else:
                            solara.Markdown("*No components registered.*")
                
                arch_decisions = d.get("architecture", {}).get("decisions", [])
                if arch_decisions:
                    with solara.Details("Architecture Decisions (Raw)"):
                        solara.Markdown(f"```json\n{json.dumps(arch_decisions, indent=2)}\n```")
