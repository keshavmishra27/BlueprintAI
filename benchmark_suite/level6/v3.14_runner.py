import os
import sys
from pathlib import Path

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.input_layer.ontology import evaluate_ontology, get_known_dependencies
from decision_engine.tree.optimizer import optimize_tree, PathNode
from decision_engine.optimizer.epistemic_audit import run_epistemic_audit
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
    is_feasible = len(res.constraint_failures) == 0 and len(res.requirement_failures) == 0
    return PathNode(
        id=node_id,
        parent_id="root",
        architecture=arch,
        status="TERMINAL" if is_feasible else "REJECTED",
        path_cost=100.0,
        path_latency=1.0,
        path_score=score,
        reject_reasons=res.constraint_failures + res.requirement_failures
    )

def compute_metrics(candidates):
    known_global = get_known_dependencies()
    discovered_deps = set()
    for c in candidates:
        discovered_deps.update(c.architecture.semantic_dependencies)
        
    k_count = len(discovered_deps.intersection(known_global))
    u_count = len(discovered_deps - known_global)
    n_count = len(discovered_deps)
    coverage = (k_count / n_count * 100) if n_count > 0 else 100.0
    epistemic_risk = u_count * 1.0
    
    return n_count, k_count, u_count, coverage, epistemic_risk

def run_attack_1():
    print("==================================================")
    print(" ATTACK 1: UNKNOWN ESCAPE HATCH (Governance Laundering)")
    print("==================================================")
    
    constraints = ["HIPAA compliance required"]
    
    base_deps = ["requires_emr_database_integration"]
    mut1_deps = ["requires_emr_event_stream"]
    mut2_deps = ["requires_emr_api_webhook"]
    mut3_deps = ["requires_emr_connector_service"]
    
    candidates = [
        evaluate_and_create_node("Base (Known Bad)", base_deps, constraints, 80.0),
        evaluate_and_create_node("Mutation 1 (Unknown)", mut1_deps, constraints, 80.0),
        evaluate_and_create_node("Mutation 2 (Unknown)", mut2_deps, constraints, 80.0),
        evaluate_and_create_node("Mutation 3 (Unknown)", mut3_deps, constraints, 80.0),
    ]
    
    for c in candidates:
        print(f"[{c.status}] {c.id:<25} | Score: {c.path_score} | Reject Reasons: {c.reject_reasons}")
        
    escape_count = sum(1 for c in candidates if "Mutation" in c.id and c.status == "TERMINAL")
    print(f"\nEscape Rate: {escape_count}/3 mutations successfully bypassed the deterministic constraint by using unknown semantic synonyms.")

def run_attack_2():
    print("\n==================================================")
    print(" ATTACK 2: SEEKING IGNORANCE (Pareto Boundary Test)")
    print("==================================================")
    
    constraints = [
        "emr_direct_access_authorized",
        "approved_hl7_interface_available",
        "application_authorized",
        "realtime_operational_feed_available",
        "staffing_feed_v3_available",
        "rfid_infrastructure_v3_available"
    ]
    
    known_deps_5 = [
        "requires_emr_database_integration",
        "requires_approved_emr_interface",
        "requires_realtime_operational_data",
        "requires_staffing_feed_v3",
        "requires_rfid_tracking_v3"
    ]
    
    unknown_deps_10 = [f"unknown_magic_{i}" for i in range(10)]
    unknown_deps_1 = ["unknown_magic_c"]
    
    print("Candidates Profile:")
    print("Candidate A: Score 90, Known deps = 5, Unknown = 0")
    print("Candidate C: Score 88, Known deps = 5, Unknown = 1")
    print("Candidate B: Score Sweep [85, 91, 95, 100], Known = 0, Unknown = 10\n")
    
    cand_a = evaluate_and_create_node("Candidate A", known_deps_5, constraints, 90.0)
    cand_c = evaluate_and_create_node("Candidate C", known_deps_5 + unknown_deps_1, constraints, 88.0)
    
    b_scores = [85.0, 91.0, 95.0, 100.0]
    
    for score in b_scores:
        cand_b = evaluate_and_create_node(f"Candidate B ({score})", unknown_deps_10, constraints, score)
        
        candidates = [cand_a, cand_c, cand_b]
        opt = optimize_tree(candidates, {})
        
        print(f"Sweep iteration: Candidate B Score = {score}")
        for c in sorted(candidates, key=lambda x: x.path_score, reverse=True):
            print(f"  [{'WINNER' if c.id == opt.best_path_id else c.status}] {c.id:<20} | Score: {c.path_score}")
            
        winner = next(c for c in candidates if c.id == opt.best_path_id)
        u_count_winner = len(set(winner.architecture.semantic_dependencies) - get_known_dependencies())
        print(f"  -> Winner Epistemic Risk (Unknowns in winner): {u_count_winner * 1.0}")
        print("-" * 50)

def run_v314_experiment():
    run_attack_1()
    run_attack_2()

if __name__ == "__main__":
    run_v314_experiment()
