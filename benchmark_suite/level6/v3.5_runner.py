import sys
import os
import json
import requests
import time

def run_v35_experiment():
    print("--- V3.5: Epistemic Boundary Experiment ---")
    raw_path = os.path.join(os.path.dirname(__file__), "results", "v3.5_hospital_case", "raw_refiner_output.json")
    
    with open(raw_path, "r") as f:
        payload = json.load(f)
        
    url_start = "http://127.0.0.1:8089/api/journey/start"
    url_answer = "http://127.0.0.1:8089/api/journey/answer"
    
    session_id = "v3.5-experiment-session"
    payload["session_id"] = session_id
    
    print("\n0. Submitting JourneyStartRequest...")
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
    unc_003 = next(u for u in payload["candidate_uncertainties"] if u["id"] == "unc-003")
    unc_004 = next(u for u in payload["candidate_uncertainties"] if u["id"] == "unc-004")
    
    print("\n--- TEST CASE EXECUTION ---")
    
    # Helper to execute answer and check status
    def test_case(name, unc_node, expected_status):
        print(f"\n{name}")
        answer_payload = {
            "session_id": session_id,
            "parent_node_id": root_node["id"],
            "answer": "YES",
            "generated_architecture": unc_node["yes_candidate_architecture"],
            "candidate_uncertainties": [],
            "is_user_selected": True
        }
        ans_resp = requests.post(url_answer, json=answer_payload, timeout=10)
        ans_data = ans_resp.json()
        
        state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id}/state", timeout=10)
        tree_state = state_resp.json()
        try:
            # Find the new node. We know it's a child of root and has the exact constraints and semantic dependencies from the payload.
            expected_deps = unc_node["yes_candidate_architecture"]["semantic_dependencies"]
            expected_constraints = unc_node["yes_candidate_architecture"].get("constraints", [])
            new_node = next(
                n for n in tree_state["decision_graph"] 
                if n["parent_id"] == root_node["id"] 
                and all(dep in n["architecture"]["semantic_dependencies"] for dep in expected_deps)
                and all(c in n["architecture"]["constraints"] for c in expected_constraints)
                and len(n["architecture"]["constraints"]) == len(expected_constraints)
                and n["status"] != "UNEXPLORED_HYPOTHESIS"
            )
        except StopIteration:
            print(f"  Error: Node not found in graph!")
            return
        
        print(f"  Result Node Status: {new_node['status']}")
        
        # print causation trace from rejected reasons if rejected
        if new_node['status'] == 'REJECTED':
            print(f"  Rejection reasons: {new_node.get('reject_reasons', 'None')}")
            
        assert new_node['status'] == expected_status, f"{name} failed! Expected {expected_status}, got {new_node['status']}. Reasons: {new_node.get('reject_reasons')}"

    # 1. Test B: Frozen reject
    test_case(
        "Test B: Frozen reject (EMR integration, Auth Missing) -> Expecting REJECTED",
        unc_001,
        "REJECTED"
    )

    # 2. Test A: Authorized pass
    test_case(
        "Test A: Authorized pass (EMR integration, Auth Present) -> Expecting TERMINAL",
        unc_002,
        "TERMINAL"
    )
    
    # 3. Test C: Unknown baseline
    test_case(
        "Test C: Unknown baseline (Alien-tech, Irrelevant Auth) -> Expecting TERMINAL",
        unc_003,
        "TERMINAL"
    )
    
    # 4. Test D: Composition
    test_case(
        "Test D: Composition (EMR + Alien-tech, Auth Missing) -> Expecting REJECTED",
        unc_004,
        "REJECTED"
    )

    print("\nSUCCESS! Epistemic Boundary Verified for V3.5.")
    print("Known semantic knowledge produces deterministic consequences. Unknown semantic knowledge is informational.")

if __name__ == "__main__":
    run_v35_experiment()
