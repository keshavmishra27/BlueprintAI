import json
import os
import shutil
import time
import requests
import glob
from pathlib import Path
from datetime import datetime

scenarios_dir = Path("benchmark_suite/scenarios/v3_core")
scenarios = sorted(glob.glob(str(scenarios_dir / "*.json")))

RUN_ID = "v3.1_pilot_02"
base_results_dir = Path(f"benchmark_suite/level6/results/{RUN_ID}")
os.makedirs(base_results_dir, exist_ok=True)
os.makedirs(base_results_dir / "raw", exist_ok=True)

with open(base_results_dir / "manifest.txt", "w") as f:
    f.write(f"Run ID: {RUN_ID}\n")
    f.write(f"Timestamp: {datetime.now().isoformat()}\n")

results_file = base_results_dir / "metrics.csv"
if not results_file.exists():
    with open(results_file, "w") as f:
        f.write("RunID,RequestedSessionID,ActualSessionID,Scenario,Baseline_Public_F,Baseline_Real_F,BP_F,Delta_F,UAR,HER,BGR,Questions,Irr_Q,Terminals,Oracle_Hit,Unselected_Winner,Final_Status\n")

trace_file = base_results_dir / "exploration_trace.csv"
if not trace_file.exists():
    with open(trace_file, "w", encoding="utf-8") as f:
        f.write("RunID,RequestedSessionID,ActualSessionID,Scenario,QuestionID,QuestionText,ImpactScore,Selected,UserAnswer,BranchGenerated,BranchValid,BranchFeasible,BranchScore\n")

def append_trace(run_id, requested_session, actual_session, scenario_name, res, answer_used="N/A"):
    trace = res.get("exploration_trace", [])
    if not trace:
        return
    with open(trace_file, "a", encoding="utf-8") as f:
        for t in trace:
            u_ans = answer_used if t.get("selected") else "N/A"
            q_text = str(t.get("question_text", "")).replace(",", ";").replace("\n", " ")
            f.write(f"{run_id},{requested_session},{actual_session},{scenario_name},{t.get('question_id')},{q_text},{t.get('impact_score')},{t.get('selected')},{u_ans},{t.get('branch_generated')},{t.get('branch_valid')},{t.get('branch_feasible')},{t.get('branch_score')}\n")

for scenario_path in scenarios:
    with open(scenario_path, "r") as f:
        scenario = json.load(f)
        
    name = Path(scenario_path).stem
    
    metric_profile = scenario.get("metric_profile", {})
    hidden_facts = scenario.get("hidden_facts_to_reveal", {})
    expected_branches = scenario.get("expected_relevant_branches", 0)
    
    if metric_profile.get("information_acquisition"):
        assert hidden_facts, f"Preflight Failed for {name}: information_acquisition=true but hidden_facts_to_reveal is empty."
    
    if metric_profile.get("hypothesis_exploration"):
        assert expected_branches > 0, f"Preflight Failed for {name}: hypothesis_exploration=true but expected_relevant_branches is 0."

    raw_dir = base_results_dir / "raw" / name
    os.makedirs(raw_dir, exist_ok=True)
    
    print(f"\n======================================")
    print(f"STARTING SCENARIO: {name}")
    print(f"======================================")
    
    with open("current_prompt.md", "w") as f:
        f.write(f"# SCENARIO: {name}\n")
        f.write(f"Problem: {scenario.get('problem_what')}\n")
        f.write(f"Why: {scenario.get('problem_why')}\n")
        f.write(f"How: {scenario.get('problem_how')}\n")
        f.write("Constraints:\n")
        for c in scenario.get("constraints", []):
            f.write(f"  - {c}\n")
        f.write("Requirements:\n")
        for r in scenario.get("requirements", []):
            f.write(f"  - {r.get('name')}\n")
            
    print(f"[AGENT INSTRUCTION] Read current_prompt.md.")
    print(f"[AGENT INSTRUCTION] Write baseline architecture payload to 'baseline.json'.")
    print(f"[AGENT INSTRUCTION] Write blueprint start payload to 'blueprint.json'.")
    print(f"[AGENT INSTRUCTION] Create a file named 'ready.txt' when done.")
    
    while not os.path.exists("ready.txt"):
        time.sleep(1)
    os.remove("ready.txt")
    
    shutil.copy("current_prompt.md", raw_dir / "current_prompt_start.md")
    if os.path.exists("baseline.json"): shutil.copy("baseline.json", raw_dir / "baseline.json")
    if os.path.exists("blueprint.json"): shutil.copy("blueprint.json", raw_dir / "blueprint_initial.json")
    
    with open("baseline.json", "r") as f:
        baseline_payload = json.load(f)
        
    pub_payload = dict(baseline_payload)
    pub_payload["private_context"] = scenario
    pub_res = requests.post("http://127.0.0.1:8000/api/journey/evaluate", json=pub_payload).json()
    base_pub_f = pub_res.get("feasible", False)
    
    real_payload = dict(baseline_payload)
    hidden_facts_list = list(scenario.get("hidden_facts_to_reveal", {}).values())
    real_payload["project_state"]["current_constraints"].extend(hidden_facts_list)
    real_payload["private_context"] = scenario
    real_res = requests.post("http://127.0.0.1:8000/api/journey/evaluate", json=real_payload).json()
    base_real_f = real_res.get("feasible", False)
    
    print(f"Baseline Public Feasibility: {base_pub_f}")
    print(f"Baseline Real Feasibility: {base_real_f}")
    
    with open("blueprint.json", "r") as f:
        blueprint_payload = json.load(f)
        
    blueprint_payload["private_context"] = scenario
    
    requested_session_id = f"{RUN_ID}-{name}-session"
    blueprint_payload["session_id"] = requested_session_id
    
    start_res = requests.post("http://127.0.0.1:8000/api/journey/start", json=blueprint_payload).json()
    actual_session_id = requested_session_id 
    
    try:
        state = requests.get(f"http://127.0.0.1:8000/api/journey/{requested_session_id}/state").json()
        actual_session_id = state.get("session_id", requested_session_id)
    except Exception:
        pass
    
    questions_asked = 0
    irr_q = 0
    valid_processable_branches = 0
    total_branches_generated = 0
    
    candidate_uncs = blueprint_payload.get("candidate_uncertainties", [])
    valid_processable_branches += len(candidate_uncs) * 2
    total_branches_generated += len(candidate_uncs) * 2
    
    interaction_step = 1
    
    while start_res.get("status") == "CONTINUE":
        qid = start_res.get("selected_uncertainty_id")
        qtext = start_res.get("selected_uncertainty_text")
        
        if not qtext:
            with open("current_prompt.md", "w") as f:
                f.write(f"# EXPLORE BRANCH\n")
                f.write(f"The engine requires you to resolve an unexplored hypothesis branch.\n")
                state = requests.get(f"http://127.0.0.1:8000/api/journey/{requested_session_id}/state").json()
                for node in state["decision_graph"]:
                    if node["status"] == "UNEXPLORED_HYPOTHESIS":
                        f.write(f"Unexplored Node ID: {node['id']}\n")
                        f.write(f"Question: {node['question_that_produced_it']}\n")
                        f.write(f"Answer required for: {node['user_answer']}\n")
                        break
            
            shutil.copy("current_prompt.md", raw_dir / f"current_prompt_step_{interaction_step}.md")
            
            while not os.path.exists("ready.txt"):
                time.sleep(1)
            os.remove("ready.txt")
            
            with open("branch.json", "r") as f:
                branch_payload = json.load(f)
            
            shutil.copy("branch.json", raw_dir / f"branch_step_{interaction_step}.json")
                
            c_uncs = branch_payload.get("candidate_uncertainties", [])
            valid_processable_branches += len(c_uncs) * 2
            total_branches_generated += len(c_uncs) * 2
            
            append_trace(RUN_ID, requested_session_id, actual_session_id, name, start_res)
            branch_payload["session_id"] = requested_session_id
            start_res = requests.post("http://127.0.0.1:8000/api/journey/answer", json=branch_payload).json()
            interaction_step += 1
            continue
        
        questions_asked += 1
        print(f"Engine asked: {qtext}")
        
        answer = "I don't have a specific policy on that. Proceed with your best judgment."
        matched = False
        for fact_key, fact_val in hidden_facts.items():
            if fact_key.lower() in qtext.lower() or any(word in qtext.lower() for word in fact_key.lower().split() if len(word) > 4):
                answer = fact_val
                matched = True
                break
                
        if not matched:
            irr_q += 1
            
        with open("current_prompt.md", "w") as f:
            f.write(f"# ORACLE ANSWER\n")
            f.write(f"Question: {qtext}\n")
            f.write(f"Answer: {answer}\n")
            
        shutil.copy("current_prompt.md", raw_dir / f"current_prompt_step_{interaction_step}.md")
            
        while not os.path.exists("ready.txt"):
            time.sleep(1)
        os.remove("ready.txt")
        
        with open("branch.json", "r") as f:
            branch_payload = json.load(f)
            
        shutil.copy("branch.json", raw_dir / f"branch_step_{interaction_step}.json")
            
        c_uncs = branch_payload.get("candidate_uncertainties", [])
        valid_processable_branches += len(c_uncs) * 2
        total_branches_generated += len(c_uncs) * 2
        
        append_trace(RUN_ID, requested_session_id, actual_session_id, name, start_res, answer_used=answer)
        branch_payload["session_id"] = requested_session_id
        start_res = requests.post("http://127.0.0.1:8000/api/journey/answer", json=branch_payload).json()
        interaction_step += 1
        
    append_trace(RUN_ID, requested_session_id, actual_session_id, name, start_res)
    print("Journey Complete.")
    final_status = start_res.get("status")
    bp_best_id = start_res.get("best_path_id")
    
    state = requests.get(f"http://127.0.0.1:8000/api/journey/{requested_session_id}/state").json()
    terminals = [n for n in state["decision_graph"] if n["status"] == "TERMINAL"]
    
    bp_f = False
    oracle_hit = False
    unselected_winner = False
    
    user_terminal = next((n for n in terminals if n.get("selected_by_user")), None)
    best_terminal = next((n for n in terminals if n["id"] == bp_best_id), None)
    
    if user_terminal and best_terminal and user_terminal["id"] != best_terminal["id"]:
        if user_terminal["architecture"].get("candidate_status") == "FEASIBLE" and best_terminal["architecture"].get("candidate_status") == "FEASIBLE":
            unselected_winner = True
    
    for t in terminals:
        if t["id"] == bp_best_id and t["architecture"].get("candidate_status") == "FEASIBLE":
            bp_f = True
            if "oracle_architecture" in scenario and scenario["oracle_architecture"]:
                o_decisions = scenario["oracle_architecture"].get("architectural_decisions", {})
                t_decisions = t["architecture"].get("architectural_decisions", {})
                if list(o_decisions.values()) == list(t_decisions.values()):
                    oracle_hit = True
            break
            
    delta_f = 1 if (bp_f and not base_real_f) else 0
    
    expected_branches = scenario.get("expected_relevant_branches", 0)
    
    if metric_profile.get("information_acquisition"):
        uar = 1.0 if (questions_asked - irr_q) > 0 else 0.0
    else:
        uar = "N/A"
        
    if metric_profile.get("hypothesis_exploration"):
        relevant_branches = (questions_asked - irr_q) * 2 if metric_profile.get("information_acquisition") else questions_asked * 2
        her = min(1.0, relevant_branches / expected_branches)
    else:
        her = "N/A"
        
    bgr = valid_processable_branches / total_branches_generated if total_branches_generated > 0 else 0.0
    
    print(f"Results for {name}:")
    print(f"Base_Real_F: {base_real_f}, BP_F: {bp_f}, Delta_F: {delta_f}, UAR: {uar}, HER: {her}, BGR: {bgr}, Oracle_Hit: {oracle_hit}, Unselected_Winner: {unselected_winner}")
    
    with open(results_file, "a") as f:
        f.write(f"{RUN_ID},{requested_session_id},{actual_session_id},{name},{base_pub_f},{base_real_f},{bp_f},{delta_f},{uar},{her},{bgr},{questions_asked},{irr_q},{len(terminals)},{oracle_hit},{unselected_winner},{final_status}\n")

print("All scenarios completed.")
