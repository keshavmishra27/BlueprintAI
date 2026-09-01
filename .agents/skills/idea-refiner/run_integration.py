import httpx
import json

base_url = "http://127.0.0.1:8089"

def build_arch_node(processing, capabilities, semantic_deps, data, resources, historical_decisions=None):
    return {
        "inputs": data,
        "processing": processing,
        "decision": ["Determine Action"],
        "output": ["Action Result"],
        "capabilities": capabilities,
        "semantic_dependencies": semantic_deps,
        "data_required": data,
        "resources_required": resources,
        "constraints": [],
        "historical_decisions": historical_decisions or []
    }

user_profile = {
    "Is external cloud processing strictly forbidden, or can we use it with strong anonymization?": "NO",
    "Are we strictly limited to the existing basic CPU computers, or can we purchase a local GPU?": "NO",
    "To meet the 7-day prototype deadline, can we drop camera integration and rely solely on existing attendance and quiz data?": "YES"
}

gemini_baseline_architecture = build_arch_node(
    processing=["Continuous Camera Ingestion", "Cloud LLM (GPT-4) for Q&A", "WhatsApp Gateway", "Autonomous Execution"],
    capabilities=["student performance tracking", "weak-topic detection", "struggling student detection", "attendance prediction", "answer arbitrary doubts", "auto-management"],
    semantic_deps=["requires_camera", "requires_cloud", "paid_api", "external_storage", "autonomous_actions", "requires_gpu", "requires_continuous_connectivity", "external_data_transfer"],
    data=["live classroom video", "student academic records", "whatsapp chat logs"],
    resources=["Cameras", "Cloud GPU", "GPT-4 API subscription"]
)

player_b_v1 = build_arch_node(
    processing=["Continuous Camera Monitoring", "Cloud LLM Analysis", "Automated WhatsApp"],
    capabilities=["student performance tracking", "weak-topic detection", "struggling student detection", "attendance prediction", "answer arbitrary doubts"],
    semantic_deps=["requires_camera", "requires_cloud", "external_storage", "requires_continuous_connectivity", "autonomous_actions"],
    data=["live classroom video", "student academic records"],
    resources=["Cameras", "Cloud GPU"],
    historical_decisions=[]
)

level_0_uncertainties = [
    {
        "id": "unc_01",
        "question_target": "Cloud Privacy",
        "unknown_fact": "Can we use cloud APIs if we anonymize data?",
        "importance": "High",
        "question_text": "Is external cloud processing strictly forbidden, or can we use it with strong anonymization?",
        "yes_mutation": {"add_constraints": ["anonymized_cloud_allowed"], "remove_constraints": []},
        "no_mutation": {"add_constraints": ["strict_no_cloud", "strict_no_external_storage"], "remove_constraints": []},
        "yes_candidate_architecture": build_arch_node(
            processing=["Continuous Camera Monitoring", "Anonymized Cloud LLM", "Teacher Approval Bot"],
            capabilities=["student performance tracking", "weak-topic detection", "struggling student detection", "attendance prediction", "answer arbitrary doubts"],
            semantic_deps=["requires_camera", "requires_cloud", "requires_continuous_connectivity"],
            data=["anonymized video", "student academic records"],
            resources=["Cameras", "Cloud GPU"]
        ),
        "no_candidate_architecture": build_arch_node(
            processing=["Local Camera Processing", "Local Student Risk Scoring", "Local Dashboard", "Teacher Approval"],
            capabilities=["student performance tracking", "weak-topic detection", "struggling student detection", "attendance prediction", "answer arbitrary doubts"],
            semantic_deps=["requires_camera", "requires_edge_gpu", "local_gpu_required"],
            data=["live classroom video", "student academic records"],
            resources=["Cameras", "Local GPU"]
        )
    }
]

level_1_uncertainties = [
    {
        "id": "unc_03",
        "question_target": "Hardware Constraint (CPU)",
        "unknown_fact": "Can the college buy GPUs?",
        "importance": "High",
        "question_text": "Are we strictly limited to the existing basic CPU computers, or can we purchase a local GPU?",
        "yes_mutation": {"add_constraints": ["gpu_purchase_allowed"], "remove_constraints": []},
        "no_mutation": {"add_constraints": ["strict_cpu_only"], "remove_constraints": []},
        "yes_candidate_architecture": build_arch_node(
            processing=["Local Camera Processing", "Local Student Risk Scoring", "Local Dashboard", "Teacher Approval"],
            capabilities=["student performance tracking", "weak-topic detection", "struggling student detection", "attendance prediction", "answer arbitrary doubts"],
            semantic_deps=["requires_camera", "requires_edge_gpu"],
            data=["live classroom video", "student academic records"],
            resources=["Cameras", "Local GPU"]
        ),
        "no_candidate_architecture": build_arch_node(
            processing=["Local Lightweight Feature Extraction", "Rule/Statistical Risk Scoring", "Local Dashboard", "Teacher Approval"],
            capabilities=["student performance tracking", "weak-topic detection", "struggling student detection", "attendance prediction", "answer arbitrary doubts"],
            semantic_deps=["requires_camera", "cpu_only_inference", "custom_hardware"],
            data=["batched images", "student academic records"],
            resources=["Cameras", "Basic College Computers"]
        )
    }
]

level_2_uncertainties = [
    {
        "id": "unc_04",
        "question_target": "Prototype Timeline",
        "unknown_fact": "Can we drop the camera requirement for the 7-day prototype?",
        "importance": "High",
        "question_text": "To meet the 7-day prototype deadline, can we drop camera integration and rely solely on existing attendance and quiz data?",
        "yes_mutation": {"add_constraints": ["no_cameras_required"], "remove_constraints": []},
        "no_mutation": {"add_constraints": ["cameras_mandatory"], "remove_constraints": []},
        "yes_candidate_architecture": build_arch_node(
            processing=["Attendance & Quiz Aggregation", "Rule-based Weakness Detection", "Local SQLite Storage", "Teacher Dashboard", "Approved WhatsApp Notification"],
            capabilities=["student performance tracking", "weak-topic detection", "struggling student detection", "attendance prediction", "answer arbitrary doubts"],
            semantic_deps=["cpu_only_inference"],
            data=["student academic records", "quiz scores", "attendance logs"],
            resources=["Basic College Computers"]
        ),
        "no_candidate_architecture": build_arch_node(
            processing=["Camera Procurement", "Lightweight Camera Extraction", "Rule/Statistical Risk Scoring", "Local Dashboard", "Teacher Approval"],
            capabilities=["student performance tracking", "weak-topic detection", "struggling student detection", "attendance prediction", "answer arbitrary doubts"],
            semantic_deps=["requires_camera", "cpu_only_inference", "custom_hardware"],
            data=["live classroom video", "student academic records"],
            resources=["Cameras", "Basic College Computers"]
        )
    }
]

def format_evaluation(eval_result, title):
    out = []
    out.append(f"#### {title}")
    
    feas_emoji = "✅" if eval_result.get('feasible', True) else "❌"
    out.append(f"**Feasible:** {feas_emoji}")
    
    if eval_result.get('constraint_violations'):
        for v in eval_result.get('constraint_violations'):
            out.append(f"  - ❌ {v}")
            
    reqs_eval = eval_result.get('requirement_evaluations', [])
    met_count = sum(1 for r in reqs_eval if r.get('satisfies', False))
    total_reqs = len(reqs_eval)
    reqs_emoji = "✅" if met_count == total_reqs else "❌"
    
    out.append(f"**Requirements:** {reqs_emoji} ({met_count}/{total_reqs})")
    
    for r in reqs_eval:
        status = "✓" if r.get('satisfies') else "❌"
        out.append(f"  - {status} {r.get('requirement')} ({r.get('reason')})")
        
    return "\n".join(out)

def format_impact(question_data):
    out = []
    q_text = question_data.get('question_text')
    impact = question_data.get('impact_score')
    b_impact = question_data.get('branch_impact', {})
    
    out.append(f"**Question Ranked:** {q_text}")
    out.append(f"**Impact Score:** {impact}")
    out.append("```text")
    out.append("YES Branch:")
    out.append(f"  feasible = {b_impact.get('yes_branch', {}).get('b_feasible')}")
    out.append(f"  requirements_met = {b_impact.get('yes_branch', {}).get('b_reqs_satisfied')}")
    out.append("NO Branch:")
    out.append(f"  feasible = {b_impact.get('no_branch', {}).get('b_feasible')}")
    out.append(f"  requirements_met = {b_impact.get('no_branch', {}).get('b_reqs_satisfied')}")
    out.append(f"Architecture changed = {b_impact.get('architecture_changed')}")
    out.append(f"Winner changed = {b_impact.get('winner_changed')}")
    out.append("```")
    return "\n".join(out)

def main():
    with open("integration_trace.md", "w", encoding="utf-8") as f:
        def prnt(text):
            f.write(text + "\n")
            
        prnt("# Controlled Agent-Stub Integration Test Trace\n")
        
        payload = {
            "what": "AI system for college (struggling detection, attendance, doubts, teacher management).",
            "why": "To improve student success and help teachers manage classes effectively.",
            "how": "Use cameras, an LLM, WhatsApp, and a dashboard. Everything should happen automatically.",
            "constraints": [
                "Very small budget",
                "Internet is unreliable",
                "Cannot store sensitive student data externally",
                "Teachers must approve important actions",
                "Prototype needed in 7 days",
                "Existing college computers are basic",
                "Should work for ~1,000 students"
            ],
            "requirements": [
                {"name": "struggling students detection", "required": True},
                {"name": "attendance prediction", "required": True},
                {"name": "answer arbitrary doubts", "required": True}
            ],
            "gemini_baseline_architecture": gemini_baseline_architecture,
            "player_b_architecture": player_b_v1,
            "uncertainties": level_0_uncertainties
        }
    
        prnt("### Level 0: Initial Evaluation\n")
        r = httpx.post(f"{base_url}/api/journey/start", json=payload, timeout=10.0)
        if r.status_code != 200:
            prnt(f"Error: {r.text}")
            return
            
        resp = r.json()
        session_id = resp.get("session_id")
        battle = resp.get("current_battle_result")
        
        prnt(format_evaluation({
            "feasible": battle.get("a_feasible"),
            "constraint_violations": battle.get("a_constraint_violations"),
            "requirement_evaluations": [{"requirement": re["requirement"], "satisfies": re["user_satisfies"], "reason": re["user_reason"]} for re in battle.get("requirement_evaluations", [])]
        }, "Player A (Gemini Baseline)"))
        prnt("\n")
        
        prnt(format_evaluation({
            "feasible": battle.get("b_feasible"),
            "constraint_violations": battle.get("b_constraint_violations"),
            "requirement_evaluations": [{"requirement": re["requirement"], "satisfies": re["player_b_satisfies"], "reason": re["player_b_reason"]} for re in battle.get("requirement_evaluations", [])]
        }, "Player B v1 (Evidence-Guided)"))
        prnt("\n")
        
        prnt(f"**Winner:** {battle.get('winner')} - {battle.get('reasoning')}\n")
        
        prnt("### Question Ranking & Selection\n")
        for q in resp.get("all_questions_scored", []):
            prnt(format_impact(q))
            prnt("")
            
        current_q = resp.get("current_question")
        if not current_q:
            prnt("No questions returned.")
            return
            
        q_text = current_q.get("question_text")
        prnt(f"**Highest Impact Question Selected:** {q_text}\n")
        
        ans = user_profile.get(q_text, "NO")
        prnt(f"**User Profile Answers:** {ans}\n")
        
        prnt(f"### Level 1: Evaluating post-answer '{ans}'\n")
        
        ans_payload = {
            "session_id": session_id,
            "selected_option": ans,
            "new_player_b_architecture": current_q.get("options", {}).get(ans, {}).get("candidate_architecture"),
            "new_uncertainties": level_1_uncertainties
        }
        
        r2 = httpx.post(f"{base_url}/api/journey/answer", json=ans_payload, timeout=10.0)
        if r2.status_code != 200:
            prnt(f"Error: {r2.text}")
            return
            
        resp2 = r2.json()
        battle2 = resp2.get("current_battle_result")
        
        prnt(format_evaluation({
            "feasible": battle2.get("b_feasible"),
            "constraint_violations": battle2.get("b_constraint_violations"),
            "requirement_evaluations": [{"requirement": re["requirement"], "satisfies": re["player_b_satisfies"], "reason": re["player_b_reason"]} for re in battle2.get("requirement_evaluations", [])]
        }, "Player B v2 (After Mutation)"))
        prnt("\n")
        prnt(f"**Winner:** {battle2.get('winner')} - {battle2.get('reasoning')}\n")
        
        prnt("### Question Ranking & Selection\n")
        for q in resp2.get("all_questions_scored", []):
            prnt(format_impact(q))
            prnt("")
            
        current_q2 = resp2.get("current_question")
        if not current_q2:
            prnt("No questions returned.")
            return
            
        q_text2 = current_q2.get("question_text")
        prnt(f"**Highest Impact Question Selected:** {q_text2}\n")
        
        ans2 = user_profile.get(q_text2, "NO")
        prnt(f"**User Profile Answers:** {ans2}\n")
        
        prnt(f"### Level 2: Evaluating post-answer '{ans2}'\n")
        
        ans_payload2 = {
            "session_id": session_id,
            "selected_option": ans2,
            "new_player_b_architecture": current_q2.get("options", {}).get(ans2, {}).get("candidate_architecture"),
            "new_uncertainties": level_2_uncertainties
        }
        
        r3 = httpx.post(f"{base_url}/api/journey/answer", json=ans_payload2, timeout=10.0)
        if r3.status_code != 200:
            prnt(f"Error: {r3.text}")
            return
            
        resp3 = r3.json()
        battle3 = resp3.get("current_battle_result")
        
        prnt(format_evaluation({
            "feasible": battle3.get("b_feasible"),
            "constraint_violations": battle3.get("b_constraint_violations"),
            "requirement_evaluations": [{"requirement": re["requirement"], "satisfies": re["player_b_satisfies"], "reason": re["player_b_reason"]} for re in battle3.get("requirement_evaluations", [])]
        }, "Player B v3 (Final Candidate)"))
        prnt("\n")
        prnt(f"**Winner:** {battle3.get('winner')} - {battle3.get('reasoning')}\n")
        
        prnt("### Question Ranking & Selection\n")
        for q in resp3.get("all_questions_scored", []):
            prnt(format_impact(q))
            prnt("")
            
        current_q3 = resp3.get("current_question")
        if not current_q3:
            prnt("No questions returned.")
            return
            
        q_text3 = current_q3.get("question_text")
        prnt(f"**Highest Impact Question Selected:** {q_text3}\n")
        
        ans3 = user_profile.get(q_text3, "YES")
        prnt(f"**User Profile Answers:** {ans3}\n")
        
        prnt(f"### Level 3: Evaluating post-answer '{ans3}'\n")
        
        ans_payload3 = {
            "session_id": session_id,
            "selected_option": ans3,
            "new_player_b_architecture": current_q3.get("options", {}).get(ans3, {}).get("candidate_architecture"),
            "new_uncertainties": [] 
        }
        
        r4 = httpx.post(f"{base_url}/api/journey/answer", json=ans_payload3, timeout=10.0)
        if r4.status_code != 200:
            prnt(f"Error: {r4.text}")
            return
            
        resp4 = r4.json()
        battle4 = resp4.get("current_battle_result")
        
        prnt(format_evaluation({
            "feasible": battle4.get("b_feasible"),
            "constraint_violations": battle4.get("b_constraint_violations"),
            "requirement_evaluations": [{"requirement": re["requirement"], "satisfies": re["player_b_satisfies"], "reason": re["player_b_reason"]} for re in battle4.get("requirement_evaluations", [])]
        }, "Player B v4 (Final Candidate)"))
        prnt("\n")
        prnt(f"**Winner:** {battle4.get('winner')} - {battle4.get('reasoning')}\n")
        prnt("## Decision Trace Table\n")
        prnt("| Level | Question | Answer | Mutation | Candidate | Feasible | Requirements | Impact |")
        prnt("|---|---|---|---|---|---|---|---|")
        
        trace = resp4.get("trace_so_far", [])
        
        for idx, entry in enumerate(trace):
            level = idx
            q_text = entry.get("question_text", "N/A")
            ans_val = entry.get("user_answer", "N/A")
            
            if idx == 0:
                b_feas = "✅" if battle2.get("b_feasible") else "❌"
                reqs = battle2.get("requirement_evaluations", [])
            elif idx == 1:
                b_feas = "✅" if battle3.get("b_feasible") else "❌"
                reqs = battle3.get("requirement_evaluations", [])
            else:
                b_feas = "✅" if battle4.get("b_feasible") else "❌"
                reqs = battle4.get("requirement_evaluations", [])
                
            passed = sum(1 for r in reqs if r.get("player_b_satisfies"))
            req_status = f"{passed}/{len(reqs)}" if reqs else "N/A"
            
            impact = entry.get("why_selected", "N/A")
            
            arch_after = entry.get("architecture_after", "")
            mutation = ", ".join(entry.get("state_mutation", [])) or "None"
            
            prnt(f"| {level} | {q_text} | {ans_val} | {mutation} | {arch_after} | {b_feas} | {req_status} | {impact} |")
            
        prnt("\n## Rejected Branches\n")
        prnt("The following branches were simulated but rejected due to feasibility/requirement failures or suboptimal impact:\n")
        
        prnt("- **Cloud Privacy (YES branch)**: Rejected because user profile answered NO.")
        prnt("- **Hardware Constraint (YES branch)**: Rejected because user profile answered NO.")
        prnt("- **Prototype Timeline (NO branch)**: Rejected because user profile answered YES.")

if __name__ == "__main__":
    main()
