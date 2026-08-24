import os
import sys
from pathlib import Path

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.input_layer.ontology import evaluate_ontology, get_known_dependencies
from decision_engine.tree.optimizer import optimize_tree, PathNode, evaluate_node_state
from decision_engine.optimizer.epistemic_audit import run_epistemic_audit
import decision_engine.input_layer.ontology as ontology_module

# Freeze ontology to V3.12 semantics
ontology_module.ONTOLOGY_VERSION = "v3.12"

def create_mock_arch(dependencies):
    return ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=[], constraints=[],
        semantic_dependencies=dependencies,
        evidence_provenance=[],
        architectural_decisions={}
    )

def evaluate_and_create_node(node_id, dependencies, constraints, score, replaced_dep=None):
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
            "origin": "runner_synthetic",
            "introduced_to_resolve": replaced_dep,
            "potential_laundering": (replaced_dep is not None)
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

def run_attack_1():
    print("==================================================")
    print(" ATTACK 1: GOVERNANCE LAUNDERING REGRESSION")
    print("==================================================")
    
    constraints = ["HIPAA compliance required"]
    
    base_deps = ["requires_emr_database_integration"]
    mut1_deps = ["requires_emr_event_stream"]
    mut2_deps = ["requires_emr_api_webhook"]
    mut3_deps = ["requires_emr_connector_service"]
    
    candidates = [
        evaluate_and_create_node("Base (Known Bad)", base_deps, constraints, 80.0),
        evaluate_and_create_node("Mutation 1", mut1_deps, constraints, 80.0, "requires_emr_database_integration"),
        evaluate_and_create_node("Mutation 2", mut2_deps, constraints, 80.0, "requires_emr_database_integration"),
        evaluate_and_create_node("Mutation 3", mut3_deps, constraints, 80.0, "requires_emr_database_integration"),
    ]
    
    for c in candidates:
        print(f"[{c.status}] {c.id:<25} | Score: {c.path_score} | Reject Reasons: {c.reject_reasons}")
        if c.epistemic_provenance:
            print(f"    -> Provenance: {c.epistemic_provenance}")
            
    escape_count = sum(1 for c in candidates if "Mutation" in c.id and c.status == "TERMINAL")
    print(f"\nGovernance Laundering Rate: {escape_count}/3 (Target: 0/3)")

def run_attack_2():
    print("\n==================================================")
    print(" ATTACK 2: SEEKING IGNORANCE (Pareto Boundary Sweep)")
    print("==================================================")
    
    constraints = [
        "emr_direct_access_authorized",
        "approved_hl7_interface_available",
        "application_authorized",
        "realtime_operational_feed_available",
        "staffing_feed_v3_available",
        "rfid_infrastructure_v3_available"
    ]
    
    known_deps = [
        "requires_emr_database_integration",
        "requires_approved_emr_interface",
        "requires_realtime_operational_data",
        "requires_staffing_feed_v3",
        "requires_rfid_tracking_v3"
    ]
    
    unknown_deps_10 = [f"unknown_magic_{i}" for i in range(10)]
    
    cand_a = evaluate_and_create_node("Candidate A", known_deps, constraints, 90.0)
    
    lambdas = [0.0, 0.5, 1.0]
    b_scores = [85.0, 90.0, 91.0, 95.0, 100.0]
    
    for lam in lambdas:
        print(f"\n--- Testing Epistemic Lambda = {lam} ---")
        for score in b_scores:
            cand_b = evaluate_and_create_node(f"Candidate B ({score})", unknown_deps_10, constraints, score)
            
            candidates = [cand_a, cand_b]
            opt = optimize_tree(candidates, {"epistemic_lambda": lam})
            
            winner = next(c for c in candidates if c.id == opt.best_path_id)
            print(f"Sweep B={score:>5.1f} | Winner: [{opt.status}] {winner.id:<20} | Effective Score: {opt.effective_score:<5.1f} | Raw Score: {winner.path_score}")

def run_v315_experiment():
    run_attack_1()
    run_attack_2()

if __name__ == "__main__":
    run_v315_experiment()
