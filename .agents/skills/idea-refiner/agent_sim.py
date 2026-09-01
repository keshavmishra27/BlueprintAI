import httpx
import json
import time

base_url = "http://127.0.0.1:8089"

def build_arch_node(processing, capabilities=None, data=None, resources=None):
    return {
        "inputs": ["Patient Arrival"],
        "processing": processing,
        "decision": ["Route to correct department"],
        "output": ["Estimated Wait Time"],
        "capabilities": capabilities or [],
        "data_required": data or [],
        "resources_required": resources or [],
        "constraints": []
    }

def run_simulation():
    print("==================================================")
    print("   IDEA REFINER - DETERMINISTIC JOURNEY SIMULATION")
    print("==================================================\n")

    print("[1] STARTING JOURNEY")
    
    player_b_v1 = build_arch_node(
        processing=["Ingest Data", "ML Prediction Model", "Display Wait Time"],
        capabilities=["Predictive Analytics"],
        data=["historical patient data"],
        resources=["GPU", "Cloud Infrastructure"]
    )
    
    uncertainties = [
        {
            "id": "unc-hist-data",
            "question_text": "Is historical patient-arrival data available for training predictive models?",
            "question_target": "historical patient data",
            "unknown_fact": "Availability of historical data",
            "importance": "High",
            "yes_mutation": {"add_constraints": ["historical patient data available"], "remove_constraints": []},
            "no_mutation": {"add_constraints": ["no historical patient data"], "remove_constraints": []},
            "yes_candidate_architecture": build_arch_node(
                processing=["Ingest Data", "ML Prediction Model", "Display Wait Time"],
                data=["historical patient data available"]
            ),
            "no_candidate_architecture": build_arch_node(
                processing=["Ingest Live Data", "Rule-based Queue", "Display Wait Time"],
                data=["live queue data"]
            )
        }
    ]

    payload = {
        "what": "Reduce hospital patient waiting time.",
        "why": "Patients wait because appointments and hospital resources aren't coordinated.",
        "how": "Maintain a queue and use an LLM to predict appointment timing.",
        "player_b_architecture": player_b_v1,
        "uncertainties": uncertainties
    }

    print("POST /api/journey/start")
    r = httpx.post(f"{base_url}/api/journey/start", json=payload, timeout=10.0)
    print(f"Status Code: {r.status_code}")
    if r.status_code != 200:
        print(r.text)
        return
        
    start_resp = r.json()
    session_id = start_resp["session_id"]
    
    print(f"Session ID: {session_id}")
    print(f"Current Architecture (Player B v1):")
    print(" -> ".join(start_resp["current_architecture"]["processing"]))
    
    if start_resp["is_complete"]:
        print("Journey finished immediately (no uncertainties).")
        return
        
    q_node = start_resp["current_question"]
    print(f"\n[2] QUESTION GENERATED")
    print(f"Decision Impact Score: {start_resp['decision_impact']}")
    print(f"Question: {q_node['question_text']}")
    print("Options:")
    for opt in q_node['options'].keys():
        print(f" - {opt}")
        
    selected_option = "NO"
    print(f"\nUser selects: {selected_option}")
    
    print("\n[3] ANSWERING QUESTION (Simulating Agent Generating v2)")
    
    player_b_v2 = build_arch_node(
        processing=["Ingest Live Data", "Rule-based Queue", "Display Wait Time"],
        capabilities=["Real-time Queue Management"],
        data=["live queue data"],
        resources=["CPU"]
    )
    
    ans_payload = {
        "session_id": session_id,
        "selected_option": selected_option,
        "new_player_b_architecture": player_b_v2,
        "new_uncertainties": []
    }
    
    r_ans = httpx.post(f"{base_url}/api/journey/answer", json=ans_payload, timeout=10.0)
    print(f"Status Code: {r_ans.status_code}")
    if r_ans.status_code != 200:
        print(r_ans.text)
        return
        
    ans_resp = r_ans.json()
    print(f"Current Architecture (Player B v2):")
    print(" -> ".join(ans_resp["current_architecture"]["processing"]))
    print(f"Constraints: {ans_resp['current_constraints']}")
    
    print("\n[4] DECISION TRACE SO FAR")
    for step in ans_resp["trace_so_far"]:
        print(f"Q: {step['question_text']}")
        print(f"A: {step['user_answer']}")
        print(f"Arch Before: {step['architecture_before']}")
        print(f"Arch After:  {step['architecture_after']}\n")
        
    print("Simulation complete! The deterministic Python engine successfully managed the state and impact.")

if __name__ == "__main__":
    run_simulation()
