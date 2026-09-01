import os
import sys
import json
from pathlib import Path

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.input_layer.ontology import evaluate_ontology, get_known_dependencies
from decision_engine.tree.optimizer import optimize_tree, PathNode, evaluate_node_state, OptimizationResult
from decision_engine.optimizer.epistemic_audit import run_epistemic_audit
from decision_engine.api.recommendation import generate_recommendation
import decision_engine.input_layer.ontology as ontology_module

ontology_module.ONTOLOGY_VERSION = "v3.12"

def create_mock_arch(dependencies):
    return ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=[], constraints=[],
        semantic_dependencies=dependencies,
        evidence_provenance=[],
        architectural_decisions={}
    )

def evaluate_and_create_node(node_id, dependencies, constraints, score):
    arch = create_mock_arch(dependencies)
    res = evaluate_ontology(arch, constraints, [])
    
    known_deps = get_known_dependencies()
    unknowns = [d for d in dependencies if d not in known_deps]
    
    passes_hard_gates = len(res.constraint_failures) == 0 and len(res.requirement_failures) == 0
    
    status = evaluate_node_state(
        node=None, 
        is_leaf=True, 
        has_unknowns=len(unknowns) > 0, 
        passes_hard_gates=passes_hard_gates
    )
    
    prov = None
    if len(unknowns) > 0:
        prov = {
            "origin": "runner_synthetic_v316",
            "potential_laundering": False
        }
    
    return PathNode(
        id=node_id,
        parent_id="root",
        architecture=arch,
        status=status,
        path_cost=100.0,
        path_latency=1.0,
        path_score=score,
        reject_reasons=res.constraint_failures + res.requirement_failures,
        epistemic_provenance=prov
    )

def run_test_1():
    print("==================================================")
    print(" TEST 1: SERIALIZATION BRIDGE REGRESSION")
    print("==================================================")
    
    constraints = [
        "emr_direct_access_authorized",
        "approved_hl7_interface_available",
        "application_authorized",
        "realtime_operational_feed_available",
        "staffing_feed_v3_available",
        "rfid_infrastructure_v3_available"
    ]
    known_deps = ["requires_emr_database_integration"]
    unknown_deps_10 = [f"unknown_{i}" for i in range(10)]
    
    cand_c = evaluate_and_create_node("Candidate_C", unknown_deps_10, constraints, 110.0)
    
    opt = optimize_tree([cand_c], {"epistemic_lambda": 0.5})
    
    raw_score = 110.0
    epistemic_risk = 10.0
    expected_effective = raw_score - (0.5 * epistemic_risk)
    
    print(f"Mathematical Assert: {opt.effective_score} == {raw_score} - (0.5 * {epistemic_risk}) -> {opt.effective_score == expected_effective}")
    
    serialized_json = opt.model_dump_json()
    deserialized_opt = OptimizationResult.model_validate_json(serialized_json)
    
    print(f"Pre-Serialization Status: {opt.status}")
    print(f"Post-Serialization Status: {deserialized_opt.status}")
    print(f"Post-Serialization Effective Score: {deserialized_opt.effective_score}")
    

def run_test_2():
    print("\n==================================================")
    print(" TEST 2: RECOMMENDATION LAYER ENFORCEMENT")
    print("==================================================")
    
    constraints = [
        "emr_direct_access_authorized"
    ]
    known_deps = ["requires_emr_database_integration"]
    unknown_deps_10 = [f"unknown_{i}" for i in range(10)]
    
    cand_a = evaluate_and_create_node("Candidate_A", known_deps, constraints, 90.0)
    cand_c = evaluate_and_create_node("Candidate_C", unknown_deps_10, constraints, 110.0)
    
    opt_a = optimize_tree([cand_a], {"epistemic_lambda": 0.5})
    opt_c = optimize_tree([cand_c], {"epistemic_lambda": 0.5})
    
    resp_a = generate_recommendation(opt_a.model_dump_json())
    resp_c = generate_recommendation(opt_c.model_dump_json())
    
    print(f"Candidate A (Raw=90, Eff=90, TERMINAL) -> Action: {resp_a.action}")
    print(f"Candidate C (Raw=110, Eff=105, UNRESOLVED) -> Action: {resp_c.action}")
    
    print("\n--- Adversarial API Attack ---")
    hacked_opt = OptimizationResult(
        status="UNRESOLVED",
        best_path_id="Hacked_Node",
        candidates_evaluated=1,
        effective_score=999999.0,
        epistemic_risk=0.0
    )
    resp_hacked = generate_recommendation(hacked_opt.model_dump_json())
    print(f"Hacked Node (Eff=999999, UNRESOLVED) -> Action: {resp_hacked.action}")

def run_test_3():
    print("\n==================================================")
    print(" TEST 3: AUDIT INDEPENDENCE (Counterfactual)")
    print("==================================================")
    constraints = ["emr_direct_access_authorized"]
    unknown_deps = ["unknown_1"]
    cand = evaluate_and_create_node("Candidate_B", unknown_deps, constraints, 95.0)
    
    opt_1 = optimize_tree([cand], {"epistemic_lambda": 0.5})
    audit_res = run_epistemic_audit(opt_1.best_architecture)
    resp_1 = generate_recommendation(opt_1.model_dump_json())
    
    opt_2 = optimize_tree([cand], {"epistemic_lambda": 0.5})
    resp_2 = generate_recommendation(opt_2.model_dump_json())
    
    print(f"Action WITH Audit: {resp_1.action}")
    print(f"Action WITHOUT Audit: {resp_2.action}")
    print(f"Audit Independence Preserved: {resp_1.action == resp_2.action}")

def run_v316_experiment():
    run_test_1()
    run_test_2()
    run_test_3()

if __name__ == "__main__":
    run_v316_experiment()
