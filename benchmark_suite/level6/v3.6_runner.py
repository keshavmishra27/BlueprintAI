import requests
import json
import time
import os
import sys

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.ontology import KNOWN_DEPENDENCIES

def run_v36_experiment():
    print("--- V3.6: Ambiguous Hospital Dependency Experiment ---")
    
    payload_path = os.path.join(os.path.dirname(__file__), "results", "v3.6_hospital_case", "raw_refiner_output.json")
    with open(payload_path, 'r') as f:
        payload = json.load(f)
        
    payload["session_id"] = "v3.6-experiment-session"
    print("\n0. Submitting JourneyStartRequest...")
    try:
        response = requests.post("http://127.0.0.1:8089/api/journey/start", json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to start journey. Is backend running on port 8089?\n{e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response body: {e.response.text}")
        return

    session_id = "v3.6-experiment-session"
    print(f"Session ID: {session_id}")
    
    state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id}/state", timeout=10)
    tree_state = state_resp.json()
    root_node = next(n for n in tree_state["decision_graph"] if n.get("parent_id") is None)
    
    # Calculate Telemetry: Ontology_Coverage
    discovered_deps = set()
    for unc in payload["candidate_uncertainties"]:
        for d in unc["yes_candidate_architecture"].get("semantic_dependencies", []):
            discovered_deps.add(d)
        for d in unc["no_candidate_architecture"].get("semantic_dependencies", []):
            discovered_deps.add(d)
            
    known_count = sum(1 for d in discovered_deps if d in KNOWN_DEPENDENCIES)
    unknown_count = len(discovered_deps) - known_count
    coverage_pct = (known_count / len(discovered_deps)) * 100 if discovered_deps else 0
    
    print("\n--- TELEMETRY: Ontology_Coverage ---")
    print(f"Discovered dependencies: {len(discovered_deps)}")
    print(f"Known: {known_count}")
    print(f"Unknown: {unknown_count}")
    print(f"Ontology coverage = {coverage_pct:.1f}%")
    
    print("\n--- TEST CASE EXECUTION ---")
    
    # 1. Test Ambiguous Unknown Dependency (YES branch)
    print("Test A: Ambiguous Unknown (requires_approved_emr_interface) -> Expecting TERMINAL (Informational)")
    req_yes = {
        "session_id": session_id,
        "parent_node_id": root_node["id"],
        "uncertainty_id": "unc-001",
        "answer": "YES",
        "candidate_uncertainties": [],
        "generated_architecture": payload["candidate_uncertainties"][0]["yes_candidate_architecture"],
        "is_user_selected": True
    }
    ans_yes_resp = requests.post("http://127.0.0.1:8089/api/journey/answer", json=req_yes, timeout=10)
    ans_yes_resp.raise_for_status()
    
    state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id}/state", timeout=10)
    tree_state = state_resp.json()
    
    node_yes = next(
        n for n in tree_state["decision_graph"] 
        if n["parent_id"] == root_node["id"] 
        and "requires_approved_emr_interface" in n["architecture"]["semantic_dependencies"]
    )
    
    print(f"  Result Node Status: {node_yes['status']}")
    print(f"  Rejection reasons: {node_yes.get('reject_reasons')}")
    
    # Acceptance Criteria Asserts
    assert node_yes['status'] == 'TERMINAL', f"Unknown dependency falsely fabricated a non-terminal status: {node_yes['status']}"
    assert not node_yes.get('reject_reasons'), f"Unknown dependency fabricated reject reasons: {node_yes.get('reject_reasons')}"
    
    # 2. Test Known Dependency (NO branch)
    print("\nTest B: Known Dependency (requires_manual_usb_transfer) -> Expecting REJECTED")
    req_no = {
        "session_id": session_id,
        "parent_node_id": root_node["id"],
        "uncertainty_id": "unc-001",
        "answer": "NO",
        "candidate_uncertainties": [],
        "generated_architecture": payload["candidate_uncertainties"][0]["no_candidate_architecture"],
        "is_user_selected": True
    }
    ans_no_resp = requests.post("http://127.0.0.1:8089/api/journey/answer", json=req_no, timeout=10)
    ans_no_resp.raise_for_status()
    
    state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id}/state", timeout=10)
    tree_state = state_resp.json()
    
    node_no = next(
        n for n in tree_state["decision_graph"] 
        if n["parent_id"] == root_node["id"] 
        and "requires_manual_usb_transfer" in n["architecture"]["semantic_dependencies"]
    )
    
    print(f"  Result Node Status: {node_no['status']}")
    assert node_no['status'] == 'REJECTED', f"Known dependency was not rejected properly. Status: {node_no['status']}"
    
    print("\nSUCCESS! V3.6 Ambiguous Hospital Dependency Verified.")
    print("The system recognizes the ontology gap and keeps the unknown dependency informational.")

if __name__ == "__main__":
    run_v36_experiment()
