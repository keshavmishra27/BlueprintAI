import sys
import os
import json
import requests
import time

def run_v34_experiment():
    print("--- V3.4: Unprompted Discovery Experiment ---")
    raw_path = os.path.join(os.path.dirname(__file__), "results", "v3.4_hospital_case_02", "raw_refiner_output.json")
    
    with open(raw_path, "r") as f:
        payload = json.load(f)
        
    url_start = "http://127.0.0.1:8089/api/journey/start"
    url_answer = "http://127.0.0.1:8089/api/journey/answer"
    
    session_id = "v3.4-experiment-session"
    payload["session_id"] = session_id
    
    print("\n1. Submitting JourneyStartRequest...")
    try:
        resp = requests.post(url_start, json=payload, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to start journey: {e}")
        return
        
    print(f"Session ID: {session_id}")
    
    state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id}/state", timeout=10)
    tree_state = state_resp.json()
    decision_graph = tree_state["decision_graph"]
    root_node = next(n for n in decision_graph if n.get("parent_id") is None)
    print(f"Root Node ID: {root_node['id']}")
    
    unc_001 = next(u for u in payload["candidate_uncertainties"] if u["id"] == "unc-001")
    unc_002 = next(u for u in payload["candidate_uncertainties"] if u["id"] == "unc-002")
    
    print("\n--- DEPENDENCY CLASSIFICATION ---")
    print(f"unc-001 (NO branch): requires_unknown_alien_tech -> Expecting UNKNOWN (Informational)")
    print(f"unc-002 (YES branch): requires_manual_usb_transfer -> Expecting KNOWN (Failure)")

    print("\n2. Testing Known Dependency: unc-002 -> YES")
    answer_payload_002 = {
        "session_id": session_id,
        "parent_node_id": root_node["id"],
        "answer": "YES",
        "generated_architecture": unc_002["yes_candidate_architecture"],
        "candidate_uncertainties": [],
        "is_user_selected": True
    }
    
    ans_resp_002 = requests.post(url_answer, json=answer_payload_002, timeout=10)
    ans_data_002 = ans_resp_002.json()
    new_node_id_002 = ans_data_002.get("new_node_id")
    
    state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id}/state", timeout=10)
    tree_state = state_resp.json()
    node_002 = next(n for n in tree_state["decision_graph"] if n["parent_id"] == root_node["id"] and "requires_manual_usb_transfer" in n["architecture"]["semantic_dependencies"])
    
    print(f"  Result Node Status: {node_002['status']}")
    assert node_002['status'] == 'REJECTED', "Known dependency failed to propagate REJECTED status!"
    
    print("\n3. Testing Unknown Dependency: unc-001 -> NO")
    answer_payload_001 = {
        "session_id": session_id,
        "parent_node_id": root_node["id"],
        "answer": "NO",
        "generated_architecture": unc_001["no_candidate_architecture"],
        "candidate_uncertainties": [],
        "is_user_selected": True
    }
    
    ans_resp_001 = requests.post(url_answer, json=answer_payload_001, timeout=10)
    ans_data_001 = ans_resp_001.json()
    
    state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id}/state", timeout=10)
    tree_state = state_resp.json()
    node_001 = next(n for n in tree_state["decision_graph"] if n["parent_id"] == root_node["id"] and "requires_unknown_alien_tech" in n["architecture"]["semantic_dependencies"])
    
    print(f"  Result Node Status: {node_001['status']}")
    assert node_001['status'] == 'TERMINAL', "Unknown dependency falsely caused a rejection!"
    
    print("\nSUCCESS! Epistemic Boundary Verified.")
    print("Known dependencies actively evaluated; Unknown dependencies treated as informational.")

if __name__ == "__main__":
    run_v34_experiment()
