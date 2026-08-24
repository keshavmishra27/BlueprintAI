import requests
import json
import os
import sys
import copy

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

def run_v37_experiment():
    print("--- V3.7: Ontology Gap Audit (Governed API) ---")
    
    # 1. Identical Input Causal Proof
    print("\n--- PART 1: IDENTICAL INPUT CAUSAL PROOF ---")
    print("Replaying exact V3.6 payload to prove the operational consequence of promotion.")
    
    v36_payload_path = os.path.join(os.path.dirname(__file__), "results", "v3.6_hospital_case", "raw_refiner_output.json")
    with open(v36_payload_path, 'r') as f:
        v36_payload = json.load(f)
        
    session_id_proof = "v3.7-proof-session"
    v36_payload["session_id"] = session_id_proof
    
    try:
        requests.post("http://127.0.0.1:8089/api/journey/start", json=v36_payload, timeout=10).raise_for_status()
        state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id_proof}/state", timeout=10)
        tree_state = state_resp.json()
        root_node = next(n for n in tree_state["decision_graph"] if n.get("parent_id") is None)
        
        req = {
            "session_id": session_id_proof,
            "parent_node_id": root_node["id"],
            "uncertainty_id": "unc-001",
            "answer": "YES",
            "candidate_uncertainties": [],
            "generated_architecture": v36_payload["candidate_uncertainties"][0]["yes_candidate_architecture"],
            "is_user_selected": True
        }
        requests.post("http://127.0.0.1:8089/api/journey/answer", json=req, timeout=10).raise_for_status()
        
        state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id_proof}/state", timeout=10)
        tree_state = state_resp.json()
        new_node = next(n for n in tree_state["decision_graph"] if n["parent_id"] == root_node["id"])
        
        print(f"V3.6 Payload (Identical Input) Result Node Status: {new_node['status']}")
        if new_node['status'] == 'REJECTED':
            print(f"Rejection reasons: {new_node.get('reject_reasons')}")
            
        assert new_node['status'] == 'REJECTED', "Expected identical input to be REJECTED due to missing authorization"
        assert "governed_api_authorization_missing" in new_node.get('reject_reasons', []), "Expected authorization missing reason"
        print("Success! V3.6 identical input is now REJECTED by V3.7 domain policy (authorization missing).")
        
    except requests.exceptions.RequestException as e:
        print(f"Failed proof run: {e}")
        return

    # 2. Matrix Validation (Constructing environment variants)
    print("\n--- PART 2: MATRIX VALIDATION (Decomposed Operational Properties) ---")
    
    def test_case(name, constraints, dependencies, expected_status, expected_reasons=None):
        print(f"\n{name}")
        payload = copy.deepcopy(v36_payload)
        session_id = f"v3.7-matrix-{name.split(':')[0].replace(' ', '')}"
        payload["session_id"] = session_id
        
        # Inject our targeted matrix variables into the payload
        # Note: In our system, the environment constraints are evaluated based on what the architecture has.
        # So we inject them into the candidate_architecture constraints.
        arch = payload["candidate_uncertainties"][0]["yes_candidate_architecture"]
        arch["constraints"] = constraints
        arch["semantic_dependencies"] = dependencies
        
        requests.post("http://127.0.0.1:8089/api/journey/start", json=payload, timeout=10).raise_for_status()
        state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id}/state", timeout=10)
        root_node = next(n for n in state_resp.json()["decision_graph"] if n.get("parent_id") is None)
        
        req = {
            "session_id": session_id,
            "parent_node_id": root_node["id"],
            "uncertainty_id": "unc-001",
            "answer": "YES",
            "candidate_uncertainties": [],
            "generated_architecture": arch,
            "is_user_selected": True
        }
        requests.post("http://127.0.0.1:8089/api/journey/answer", json=req, timeout=10).raise_for_status()
        
        state_resp = requests.get(f"http://127.0.0.1:8089/api/journey/{session_id}/state", timeout=10)
        new_node = next(n for n in state_resp.json()["decision_graph"] if n["parent_id"] == root_node["id"])
        
        print(f"  Result Node Status: {new_node['status']}")
        if new_node['status'] == 'REJECTED':
            print(f"  Rejection reasons: {new_node.get('reject_reasons')}")
            
        assert new_node['status'] == expected_status, f"{name} failed! Expected {expected_status}, got {new_node['status']}"
        if expected_reasons:
            reasons = new_node.get('reject_reasons') or []
            assert all(r in reasons for r in expected_reasons), f"Expected {expected_reasons}, got {reasons}"

    # Case A: Available, Authorized, Freshness Yes -> TERMINAL
    test_case(
        "Case A: Authorized + Real-time feed available",
        constraints=["approved_hl7_interface_available", "application_authorized", "realtime_operational_feed_available"],
        dependencies=["requires_approved_emr_interface", "requires_realtime_operational_data"],
        expected_status="TERMINAL"
    )
    
    # Case B: Available, Not Authorized, Freshness Yes -> REJECTED
    test_case(
        "Case B: Missing Authorization",
        constraints=["approved_hl7_interface_available", "realtime_operational_feed_available"],
        dependencies=["requires_approved_emr_interface", "requires_realtime_operational_data"],
        expected_status="REJECTED",
        expected_reasons=["governed_api_authorization_missing"]
    )
    
    # Case C: Authorized, Freshness No -> REJECTED
    test_case(
        "Case C: Missing Real-time feed",
        constraints=["approved_hl7_interface_available", "application_authorized"],
        dependencies=["requires_approved_emr_interface", "requires_realtime_operational_data"],
        expected_status="REJECTED",
        expected_reasons=["realtime_feed_unavailable"]
    )
    
    # Case D: Unknown dependency -> INFORMATIONAL
    test_case(
        "Case D: Unknown Dependency",
        constraints=["approved_hl7_interface_available", "application_authorized", "realtime_operational_feed_available"],
        dependencies=["requires_alien_telepathy"],
        expected_status="TERMINAL"
    )

    print("\nSUCCESS! V3.7 Decomposition Verified.")

if __name__ == "__main__":
    run_v37_experiment()
