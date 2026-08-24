import requests
import json
import os
from pprint import pprint

BASE_URL = "http://127.0.0.1:8089"
SESSION_ID = "v3.2c-diagnostic-session"
RESULTS_DIR = "d:/kfiles/BlueprintAI/benchmark_suite/level6/results/v3.2_hospital_case_01"

def run_diagnostic():
    print(f"--- Starting V3.2-C Diagnostic ---")
    
    # 1. Load the frozen refiner output
    with open(f"{RESULTS_DIR}/raw_refiner_output.json", "r") as f:
        payload = json.load(f)
        
    payload["session_id"] = SESSION_ID
    
    # 2. Start Journey
    print("1. Submitting JourneyStartRequest...")
    start_resp = requests.post(f"{BASE_URL}/api/journey/start", json=payload)
    if start_resp.status_code != 200:
        print(f"Start failed: {start_resp.text}")
        return
        
    start_data = start_resp.json()
    print(f"Start Status: {start_data['status']}")
    
    # Get State to find root node ID
    state_resp = requests.get(f"{BASE_URL}/api/journey/{SESSION_ID}/state")
    tree_state = state_resp.json()
    decision_graph = tree_state["decision_graph"]
    
    # The root node has parent_id = None
    root_node = next(n for n in decision_graph if n.get("parent_id") is None)
    current_parent_id = root_node["id"]
    
    print(f"Root Node ID (S0): {current_parent_id}")
    
    # 3. Iterate through uncertainties and supply "NO" sequentially
    uncertainties = payload["candidate_uncertainties"]
    
    for idx, unc in enumerate(uncertainties):
        unc_id = unc["id"]
        print(f"\n--- Processing {unc_id} -> NO ---")
        
        answer_req = {
            "session_id": SESSION_ID,
            "parent_node_id": current_parent_id,
            "answer": "NO",
            "generated_architecture": unc["no_candidate_architecture"],
            "candidate_uncertainties": [], # No new uncertainties
            "is_user_selected": True
        }
        
        ans_resp = requests.post(f"{BASE_URL}/api/journey/answer", json=answer_req)
        if ans_resp.status_code != 200:
            print(f"Answer failed: {ans_resp.text}")
            return
            
        ans_data = ans_resp.json()
        print(f"Answer Status: {ans_data['status']}")
        
        # Get State to find the newly created node
        state_resp = requests.get(f"{BASE_URL}/api/journey/{SESSION_ID}/state")
        tree_state = state_resp.json()
        decision_graph = tree_state["decision_graph"]
        
        # Find the node we just created
        new_node = next(n for n in decision_graph if n.get("parent_id") == current_parent_id and n.get("user_answer") == "NO" and n.get("status") != "UNEXPLORED_HYPOTHESIS")
        current_parent_id = new_node["id"]
        
        print(f"New Node ID: {current_parent_id}")
        print(f"Node Status: {new_node['status']}")
        print(f"Semantic Dependencies: {new_node['architecture']['semantic_dependencies']}")
        print(f"Best Path ID according to optimizer: {ans_data.get('best_path_id')}")
        
    print("\n--- Final Diagnostic State ---")
    
    # Print the terminal candidates and best_path_id
    state_resp = requests.get(f"{BASE_URL}/api/journey/{SESSION_ID}/state")
    tree_state = state_resp.json()
    decision_graph = tree_state["decision_graph"]
    
    terminal_nodes = [n for n in decision_graph if n["status"] == "TERMINAL"]
    print(f"Total Terminal Nodes: {len(terminal_nodes)}")
    
    for n in terminal_nodes:
        print(f"Terminal Node: {n['id']} | Feasible: {True if n.get('path_score', 0) > 0 else 'CHECK_RULES'} | Dependencies: {n['architecture']['semantic_dependencies']}")
        
    # Save the final decision graph to inspect later
    with open(f"{RESULTS_DIR}/v3.2c_final_state.json", "w") as f:
        json.dump(tree_state, f, indent=2)
        
    print(f"Final state saved to {RESULTS_DIR}/v3.2c_final_state.json")

if __name__ == "__main__":
    run_diagnostic()
