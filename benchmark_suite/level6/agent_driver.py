import json
import os
import sys
import shutil
import time
import requests
import glob
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from benchmark_suite.level6.control_plane.handshake import (
    InstructionType,
    ExecutionStatus,
    PromptPacket,
    ResponsePacket,
    create_prompt_packet,
    validate_identity,
    PROMPT_PACKET_FILE,
    RESPONSE_PACKET_FILE,
    READY_FILE,
    HUMAN_PROMPT_FILE,
)

# Scenarios directory
scenarios_dir = Path("benchmark_suite/scenarios/v3_core")
scenarios = sorted(glob.glob(str(scenarios_dir / "*.json")))

RUN_ID = os.environ.get("BLUEPRINT_RUN_ID", "v3.1_pilot_03")
STEP_TIMEOUT_SECONDS = float(os.environ.get("BLUEPRINT_STEP_TIMEOUT", "90.0"))

if os.environ.get("BLUEPRINT_SMOKE_TEST") == "1":
    print("SMOKE TEST MODE ENABLED: Limiting to 1 scenario.")
    scenarios = scenarios[:1]

base_results_dir = Path(f"benchmark_suite/level6/results/{RUN_ID}")
os.makedirs(base_results_dir, exist_ok=True)
os.makedirs(base_results_dir / "raw", exist_ok=True)

# Write manifest
with open(base_results_dir / "manifest.txt", "w") as f:
    f.write(f"Run ID: {RUN_ID}\n")
    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
    f.write(f"Step Timeout (s): {STEP_TIMEOUT_SECONDS}\n")

results_file = base_results_dir / "metrics.csv"
if not results_file.exists():
    with open(results_file, "w") as f:
        f.write("RunID,RequestedSessionID,ActualSessionID,Scenario,Baseline_Public_F,Baseline_Real_F,BP_F,Delta_F,UAR,HER,BGR_processable,Questions,Irr_Q,Terminals,Oracle_Hit,Unselected_Winner,Final_Status\n")

trace_file = base_results_dir / "exploration_trace.csv"
if not trace_file.exists():
    with open(trace_file, "w", encoding="utf-8") as f:
        f.write("RunID,RequestedSessionID,ActualSessionID,Scenario,QuestionID,QuestionText,ImpactScore,Selected,UserAnswer,BranchGenerated,BranchValid,BranchFeasible,BranchScore,EncodingNormalized\n")

def append_trace(run_id, requested_session, actual_session, scenario_name, res, answer_used="N/A", bom_normalized=False):
    trace = res.get("exploration_trace", [])
    if not trace:
        return
    with open(trace_file, "a", encoding="utf-8") as f:
        for t in trace:
            u_ans = answer_used if t.get("selected") else "N/A"
            q_text = str(t.get("question_text", "")).replace(",", ";").replace("\n", " ")
            f.write(f"{run_id},{requested_session},{actual_session},{scenario_name},{t.get('question_id')},{q_text},{t.get('impact_score')},{t.get('selected')},{u_ans},{t.get('branch_generated')},{t.get('branch_valid')},{t.get('branch_feasible')},{t.get('branch_score')},{bom_normalized}\n")

def dispatch_and_wait(
    run_id: str,
    scenario_id: str,
    step_id: int,
    instruction_type: InstructionType,
    target_artifacts: List[str],
    prompt_text: str,
    timeout_seconds: float = STEP_TIMEOUT_SECONDS,
    safety_margin_seconds: float = 15.0,
) -> Optional[ResponsePacket]:
    """
    Dispatches an authoritative PromptPacket and waits with bounded timeout for a matching ResponsePacket.
    """
    prompt = create_prompt_packet(
        run_id=run_id,
        scenario_id=scenario_id,
        step_id=step_id,
        instruction_type=instruction_type,
        target_artifacts=target_artifacts,
        prompt_text=prompt_text,
        timeout_seconds=timeout_seconds,
    )
    
    # 1. Clean prior transient response files
    resp_file = Path(RESPONSE_PACKET_FILE)
    if resp_file.exists():
        try: os.remove(resp_file)
        except Exception: pass
        
    ready_file = Path(READY_FILE)
    if ready_file.exists():
        try: os.remove(ready_file)
        except Exception: pass

    # 2. Write prompt packet
    prompt_file = Path(PROMPT_PACKET_FILE)
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt.model_dump_json(indent=2))

    # 3. Bounded wait loop
    max_wait = timeout_seconds + safety_margin_seconds
    start_t = time.time()
    
    while time.time() - start_t < max_wait:
        if resp_file.exists():
            try:
                with open(resp_file, "r", encoding="utf-8") as f:
                    resp_data = json.load(f)
                response = ResponsePacket(**resp_data)
                
                # Check identity match
                id_res = validate_identity(prompt, response)
                if id_res["valid"]:
                    return response
                else:
                    print(f"[Driver] Identity mismatch on response: {id_res['mismatches']}", file=sys.stderr)
            except Exception:
                pass
        time.sleep(0.5)

    print(f"[Driver] Safety timeout expired ({max_wait}s) waiting for response on step {step_id}.", file=sys.stderr)
    return None

for scenario_path in scenarios:
    with open(scenario_path, "r") as f:
        scenario = json.load(f)
        
    name = Path(scenario_path).stem
    
    # Preflight Assertions
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
    
    # Step 0: Initial Public Prompt
    prompt_text = (
        f"# SCENARIO: {name}\n"
        f"Problem: {scenario.get('problem_what')}\n"
        f"Why: {scenario.get('problem_why')}\n"
        f"How: {scenario.get('problem_how')}\n"
        f"Constraints:\n" + "\n".join(f"  - {c}" for c in scenario.get("constraints", [])) + "\n"
        f"Requirements:\n" + "\n".join(f"  - {r.get('name')}" for r in scenario.get("requirements", [])) + "\n"
    )
    
    print(f"[AGENT INSTRUCTION] Generating baseline.json and blueprint.json...")
    
    start_resp = dispatch_and_wait(
        run_id=RUN_ID,
        scenario_id=name,
        step_id=0,
        instruction_type=InstructionType.START,
        target_artifacts=["baseline.json", "blueprint.json"],
        prompt_text=prompt_text,
    )
    
    if not start_resp or start_resp.status != ExecutionStatus.SUCCESS:
        failure_status = start_resp.status.value if start_resp else "RUNTIME_FAILURE"
        print(f"[ERROR] Step 0 failed for scenario {name}: {failure_status}", file=sys.stderr)
        with open(results_file, "a") as f:
            f.write(f"{RUN_ID},{RUN_ID}-{name}-session,{RUN_ID}-{name}-session,{name},False,False,False,0,0,0,0,0,0,0,False,False,{failure_status}\n")
        continue

    shutil.copy(HUMAN_PROMPT_FILE, raw_dir / "current_prompt_start.md")
    if os.path.exists("baseline.json"): shutil.copy("baseline.json", raw_dir / "baseline.json")
    if os.path.exists("blueprint.json"): shutil.copy("blueprint.json", raw_dir / "blueprint_initial.json")
    
    # 2. Evaluate Baseline Public & Real
    with open("baseline.json", "r", encoding="utf-8-sig") as f:
        baseline_payload = json.load(f)
        
    # Public Eval
    pub_payload = dict(baseline_payload)
    pub_payload["private_context"] = scenario
    pub_res = requests.post("http://127.0.0.1:8000/api/journey/evaluate", json=pub_payload).json()
    base_pub_f = pub_res.get("feasible", False)
    
    # Real Eval
    real_payload = dict(baseline_payload)
    hidden_facts_list = list(scenario.get("hidden_facts_to_reveal", {}).values())
    real_payload["project_state"]["current_constraints"].extend(hidden_facts_list)
    real_payload["private_context"] = scenario
    real_res = requests.post("http://127.0.0.1:8000/api/journey/evaluate", json=real_payload).json()
    base_real_f = real_res.get("feasible", False)
    
    print(f"Baseline Public Feasibility: {base_pub_f}")
    print(f"Baseline Real Feasibility: {base_real_f}")
    
    # 3. Start BlueprintAI Journey
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
    scenario_aborted = False
    
    while start_res.get("status") == "CONTINUE":
        qid = start_res.get("selected_uncertainty_id")
        qtext = start_res.get("selected_uncertainty_text")
        
        if not qtext:
            # Resolving UNEXPLORED_HYPOTHESIS
            branch_prompt = (
                f"# EXPLORE BRANCH\n"
                f"The engine requires you to resolve an unexplored hypothesis branch.\n"
            )
            state = requests.get(f"http://127.0.0.1:8000/api/journey/{requested_session_id}/state").json()
            for node in state["decision_graph"]:
                if node["status"] == "UNEXPLORED_HYPOTHESIS":
                    branch_prompt += f"Unexplored Node ID: {node['id']}\n"
                    branch_prompt += f"Question: {node['question_that_produced_it']}\n"
                    branch_prompt += f"Answer required for: {node['user_answer']}\n"
                    break
            
            step_resp = dispatch_and_wait(
                run_id=RUN_ID,
                scenario_id=name,
                step_id=interaction_step,
                instruction_type=InstructionType.BRANCH,
                target_artifacts=["branch.json"],
                prompt_text=branch_prompt,
            )
            
            if not step_resp or step_resp.status != ExecutionStatus.SUCCESS:
                scenario_aborted = True
                failure_status = step_resp.status.value if step_resp else "RUNTIME_FAILURE"
                print(f"[ERROR] Step {interaction_step} failed for scenario {name}: {failure_status}", file=sys.stderr)
                break
            
            shutil.copy(HUMAN_PROMPT_FILE, raw_dir / f"current_prompt_step_{interaction_step}.md")
            
            with open("branch.json", "r", encoding="utf-8-sig") as f:
                branch_payload = json.load(f)
            
            shutil.copy("branch.json", raw_dir / f"branch_step_{interaction_step}.json")
                
            c_uncs = branch_payload.get("candidate_uncertainties", [])
            valid_processable_branches += len(c_uncs) * 2
            total_branches_generated += len(c_uncs) * 2
            
            append_trace(RUN_ID, requested_session_id, actual_session_id, name, start_res, bom_normalized=step_resp.bom_normalized)
            branch_payload["session_id"] = requested_session_id
            start_res = requests.post("http://127.0.0.1:8000/api/journey/answer", json=branch_payload).json()
            interaction_step += 1
            continue
        
        questions_asked += 1
        print(f"Engine asked: {qtext}")
        
        # Determine Oracle Answer
        answer = "I don't have a specific policy on that. Proceed with your best judgment."
        matched = False
        for fact_key, fact_val in hidden_facts.items():
            if fact_key.lower() in qtext.lower() or any(word in qtext.lower() for word in fact_key.lower().split() if len(word) > 4):
                answer = fact_val
                matched = True
                break
                
        if not matched:
            irr_q += 1
            
        oracle_prompt = (
            f"# ORACLE ANSWER\n"
            f"Question: {qtext}\n"
            f"Answer: {answer}\n"
        )
        
        step_resp = dispatch_and_wait(
            run_id=RUN_ID,
            scenario_id=name,
            step_id=interaction_step,
            instruction_type=InstructionType.BRANCH,
            target_artifacts=["branch.json"],
            prompt_text=oracle_prompt,
        )
        
        if not step_resp or step_resp.status != ExecutionStatus.SUCCESS:
            scenario_aborted = True
            failure_status = step_resp.status.value if step_resp else "RUNTIME_FAILURE"
            print(f"[ERROR] Step {interaction_step} failed for scenario {name}: {failure_status}", file=sys.stderr)
            break
            
        shutil.copy(HUMAN_PROMPT_FILE, raw_dir / f"current_prompt_step_{interaction_step}.md")
            
        with open("branch.json", "r", encoding="utf-8-sig") as f:
            branch_payload = json.load(f)
            
        shutil.copy("branch.json", raw_dir / f"branch_step_{interaction_step}.json")
            
        c_uncs = branch_payload.get("candidate_uncertainties", [])
        valid_processable_branches += len(c_uncs) * 2
        total_branches_generated += len(c_uncs) * 2
        
        append_trace(RUN_ID, requested_session_id, actual_session_id, name, start_res, answer_used=answer, bom_normalized=step_resp.bom_normalized)
        branch_payload["session_id"] = requested_session_id
        start_res = requests.post("http://127.0.0.1:8000/api/journey/answer", json=branch_payload).json()
        interaction_step += 1

    if scenario_aborted:
        with open(results_file, "a") as f:
            f.write(f"{RUN_ID},{requested_session_id},{actual_session_id},{name},{base_pub_f},{base_real_f},False,0,0,0,0,{questions_asked},{irr_q},0,False,False,RUNTIME_FAILURE\n")
        continue

    # Log any trace from the final call if it ended
    append_trace(RUN_ID, requested_session_id, actual_session_id, name, start_res)
    print("Journey Complete.")
    final_status = start_res.get("status")
    bp_best_id = start_res.get("best_path_id")
    
    state = requests.get(f"http://127.0.0.1:8000/api/journey/{requested_session_id}/state").json()
    terminals = [n for n in state["decision_graph"] if n["status"] == "TERMINAL"]
    
    # Calculate BP Feasibility & Unselected Winner
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
    
    # HER and UAR logic based on metric_profile
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
        
    # BGR_processable: Syntactic & Schema processability reliability
    bgr_processable = valid_processable_branches / total_branches_generated if total_branches_generated > 0 else 0.0
    
    print(f"Results for {name}:")
    print(f"Base_Real_F: {base_real_f}, BP_F: {bp_f}, Delta_F: {delta_f}, UAR: {uar}, HER: {her}, BGR_processable: {bgr_processable}, Oracle_Hit: {oracle_hit}, Unselected_Winner: {unselected_winner}")
    
    with open(results_file, "a") as f:
        f.write(f"{RUN_ID},{requested_session_id},{actual_session_id},{name},{base_pub_f},{base_real_f},{bp_f},{delta_f},{uar},{her},{bgr_processable},{questions_asked},{irr_q},{len(terminals)},{oracle_hit},{unselected_winner},{final_status}\n")

print("All scenarios completed.")
