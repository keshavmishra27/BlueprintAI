import os
import sys
import copy
import json
from pathlib import Path

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import PathNode, optimize_tree, OptimizationResult
from decision_engine.tree.context import DecisionContext
from decision_engine.api.recommendation import generate_recommendation
import decision_engine.input_layer.ontology as ontology_module

ontology_module.ONTOLOGY_VERSION = "v3.12"

def create_mock_arch():
    return ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=[], constraints=[],
        semantic_dependencies=["requires_emr_database_integration"],
        evidence_provenance=[],
        architectural_decisions={}
    )

def print_test_header(test_num, title):
    print(f"\n==================================================")
    print(f" TEST {test_num}: {title}")
    print(f"==================================================")

def run_v319_experiment():
    print("==================================================")
    print(" V3.19: TEMPORAL GOVERNANCE & STALE-BLUEPRINT")
    print("==================================================")
    
    base_env_constraints = ["emr_direct_access_authorized", "staffing_api_authorized"]
    
    ctx_base = DecisionContext(
        ontology_version="v3.12",
        registry_policy_hashes=["hash_policy_1"],
        environment_constraints=base_env_constraints,
        optimizer_preferences={"epistemic_lambda": 0.5}
    )
    
    node = PathNode(
        id="Cand_A",
        parent_id="root",
        architecture=create_mock_arch(),
        status="TERMINAL",
        path_cost=100.0,
        path_score=90.0,
        reject_reasons=[],
        epistemic_provenance=None
    )
    
    print_test_header(1, "Initial Validity (Control)")
    opt_1 = optimize_tree([node], ctx_base)
    opt_1_json = opt_1.model_dump_json()
    resp_1 = generate_recommendation(opt_1_json, ctx_base)
    print(f"Action: {resp_1.action} | Reason: {resp_1.epistemic_warnings}")
    
    print_test_header(2, "Environment Mutation Stale Replay")
    ctx_env_stale = DecisionContext(
        ontology_version="v3.12",
        registry_policy_hashes=["hash_policy_1"],
        environment_constraints=["emr_direct_access_authorized"],
        optimizer_preferences={"epistemic_lambda": 0.5}
    )
    resp_2 = generate_recommendation(opt_1_json, ctx_env_stale)
    print(f"Action: {resp_2.action} | Reason: {resp_2.epistemic_warnings}")

    print_test_header(3, "Ontology/Policy Mutation Stale Replay")
    ctx_policy_stale = DecisionContext(
        ontology_version="v3.12",
        registry_policy_hashes=["hash_policy_1", "hash_policy_2"],
        environment_constraints=base_env_constraints,
        optimizer_preferences={"epistemic_lambda": 0.5}
    )
    resp_3 = generate_recommendation(opt_1_json, ctx_policy_stale)
    print(f"Action: {resp_3.action} | Reason: {resp_3.epistemic_warnings}")

    print_test_header(4, "Preference Mutation Stale Replay")
    ctx_pref_stale = DecisionContext(
        ontology_version="v3.12",
        registry_policy_hashes=["hash_policy_1"],
        environment_constraints=base_env_constraints,
        optimizer_preferences={"epistemic_lambda": 1.0}
    )
    resp_4 = generate_recommendation(opt_1_json, ctx_pref_stale)
    print(f"Action: {resp_4.action} | Reason: {resp_4.epistemic_warnings}")
    
    print_test_header(5, "Identical State Control Replay")
    ctx_identical = DecisionContext(
        ontology_version="v3.12",
        registry_policy_hashes=["hash_policy_1"],
        environment_constraints=["emr_direct_access_authorized", "staffing_api_authorized"],
        optimizer_preferences={"epistemic_lambda": 0.5}
    )
    resp_5 = generate_recommendation(opt_1_json, ctx_identical)
    print(f"Action: {resp_5.action} | Reason: {resp_5.epistemic_warnings}")
    
    print_test_header(6, "Semantically Equivalent Context Replay")
    ctx_equiv = DecisionContext(
        ontology_version="v3.12",
        registry_policy_hashes=["hash_policy_1"],
        environment_constraints=["staffing_api_authorized", "emr_direct_access_authorized"],
        optimizer_preferences={"epistemic_lambda": 0.5}
    )
    resp_6 = generate_recommendation(opt_1_json, ctx_equiv)
    print(f"Action: {resp_6.action} | Reason: {resp_6.epistemic_warnings}")
    
    print_test_header(7, "Malicious Decision Alteration")
    malicious_opt_dict = json.loads(opt_1_json)
    malicious_opt_dict["best_architecture"]["semantic_dependencies"] = ["requires_quantum_hospital_network"]
    malicious_opt_json = json.dumps(malicious_opt_dict)
    
    resp_7 = generate_recommendation(malicious_opt_json, ctx_base)
    print(f"Action: {resp_7.action} | Reason: {resp_7.epistemic_warnings}")

if __name__ == "__main__":
    run_v319_experiment()
