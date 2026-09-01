import sys
import os
import json
import requests
import time

def run_replay():
    print("--- V3.3-D Identical-Input Replay ---")
    raw_path = os.path.join(os.path.dirname(__file__), "results", "v3.2_hospital_case_01", "raw_refiner_output.json")
    expectations_path = os.path.join(os.path.dirname(__file__), "results", "v3.2_hospital_case_01", "v3.2_regression_expectations.json")
    
    with open(raw_path, "r") as f:
        payload = json.load(f)
        
    with open(expectations_path, "r") as f:
        expectations = json.load(f)
        
    url_start = "http://127.0.0.1:8089/api/journey/start"
    url_answer = "http://127.0.0.1:8089/api/journey/answer"
    
    payload["session_id"] = "v3.3d-replay-session"
    
    print("Submitting JourneyStartRequest...")
    try:
        resp = requests.post(url_start, json=payload, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to start journey: {e}")
        return
        
    data = resp.json()
    session_id = "v3.3d-replay-session"
    print(f"Session ID: {session_id}")
    
    state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id}/state", timeout=10)
    tree_state = state_resp.json()
    decision_graph = tree_state["decision_graph"]
    root_node = next(n for n in decision_graph if n.get("parent_id") is None)
    
    unc_002 = next(u for u in payload["candidate_uncertainties"] if u["id"] == "unc-002")
    
    print("\nAnswering unc-002 -> NO")
    answer_payload = {
        "session_id": session_id,
        "parent_node_id": root_node["id"],
        "answer": "NO",
        "generated_architecture": unc_002["no_candidate_architecture"],
        "candidate_uncertainties": [],
        "is_user_selected": True
    }
    
    try:
        ans_resp = requests.post(url_answer, json=answer_payload, timeout=10)
        ans_resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to submit answer: {e}")
        return
        
    ans_data = ans_resp.json()
    print(f"ans_data: {ans_data}")
    new_node_id = ans_data.get("new_node_id")
    if not new_node_id:
        pass
    
    state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id}/state", timeout=10)
    tree_state = state_resp.json()
    new_node = next(n for n in tree_state["decision_graph"] if n["parent_id"] == root_node["id"])
    
    print("\n--- Verifying Causal Repaired State ---")
    print(f"Node Status: {new_node.get('status')}")
    print(f"Semantic Dependencies: {new_node.get('architecture', {}).get('semantic_dependencies')}")
    
    expected = expectations["unc-002_NO"]
    print(f"\nV3.2 Expected Node Status: {expected['node_status']}")
    print(f"V3.3 Actual Node Status: {new_node.get('status')}")
    
    assert new_node.get("status") == "REJECTED", "Node status did not propagate to REJECTED"
    
    print("\nReplay SUCCESS. Identical input produced corrected state.")

if __name__ == "__main__":
    run_replay()
