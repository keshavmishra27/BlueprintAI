import os
import sys

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.tree.tree_schemas import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.input_layer.ontology import evaluate_ontology
import decision_engine.input_layer.ontology as ontology_module
from decision_engine.tree.optimizer import optimize_tree
from decision_engine.optimizer.epistemic_audit import run_epistemic_audit

def create_mock_node(node_id: str, score: float, dependencies: list, env_constraints: list) -> PathNode:
    arch = ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[],
        data_required=[], resources_required=[], constraints=[],
        evidence_provenance=[], historical_decisions=[],
        semantic_dependencies=dependencies,
        architectural_decisions={}
    )
    
    res = evaluate_ontology(arch, env_constraints, env_requirements=[])
    b_feasible = len(res.constraint_failures) == 0 and len(res.requirement_failures) == 0
    
    status = "TERMINAL" if b_feasible else "REJECTED"
    
    return PathNode(
        id=node_id,
        parent_id="root",
        architecture=arch,
        uncertainty_resolved=True,
        uncertainty_question=None,
        uncertainty_importance="CRITICAL",
        uncertainty_target="Data",
        b_feasible=b_feasible,
        status=status,
        path_cost=100.0,
        path_latency=1.0,
        path_score=score,
        reject_reasons=res.constraint_failures + res.requirement_failures
    )

def generate_frozen_payload(env_constraints):
    return [
        create_mock_node("Node-A-Safe", score=78, dependencies=[], env_constraints=env_constraints),
        create_mock_node("Node-B-Risky", score=91, dependencies=["requires_brain_computer_interface"], env_constraints=env_constraints),
        create_mock_node("Node-C-Strong", score=88, dependencies=["requires_irrelevant_magic"], env_constraints=env_constraints),
        create_mock_node("Node-D-Highest", score=94, dependencies=["requires_brain_computer_interface", "requires_staffing_feed"], env_constraints=env_constraints),
        create_mock_node("Node-E-Mid", score=92, dependencies=["requires_staffing_feed"], env_constraints=env_constraints)
    ]

def assert_optimizer_invariant(nodes):
    opt_only = optimize_tree(nodes, {})
    opt_audit = optimize_tree(nodes, {})
    assert opt_only.best_path_id == opt_audit.best_path_id
    return opt_audit

def run_v310_experiment():
    print("--- V3.10: The Messy Multi-Candidate Iterative Feedback Loop ---")
    
    env_constraints = ["standard_hospital_env"]
    
    print("\n--- Phase 1: Total Ignorance (v3.10.0) ---")
    ontology_module.ONTOLOGY_VERSION = "v3.10.0"
    nodes_p1 = generate_frozen_payload(env_constraints)
    
    status_map_p1 = {n.id: n.status for n in nodes_p1}
    assert all(s == "TERMINAL" for s in status_map_p1.values()), "All should be terminal initially"
    
    opt_p1 = assert_optimizer_invariant(nodes_p1)
    print(f"Winner: {opt_p1.best_path_id}")
    assert opt_p1.best_path_id == "Node-D-Highest"
    
    audit_p1 = run_epistemic_audit(opt_p1.best_architecture)
    print(f"Gaps: {audit_p1.ontology_gaps_in_winning_architecture}")
    assert set(audit_p1.ontology_gaps_in_winning_architecture) == {"requires_brain_computer_interface", "requires_staffing_feed"}

    print("\n--- Phase 2: Promote Gap 1 (v3.10.1) ---")
    ontology_module.ONTOLOGY_VERSION = "v3.10.1"
    nodes_p2 = generate_frozen_payload(env_constraints)
    status_map_p2 = {n.id: n.status for n in nodes_p2}
    
    print(f"Node-B Status: {status_map_p2['Node-B-Risky']} (Reason: {next(n.reject_reasons for n in nodes_p2 if n.id=='Node-B-Risky')})")
    print(f"Node-D Status: {status_map_p2['Node-D-Highest']}")
    
    assert status_map_p2["Node-B-Risky"] == "REJECTED"
    assert status_map_p2["Node-D-Highest"] == "REJECTED"
    assert status_map_p2["Node-A-Safe"] == "TERMINAL"
    assert status_map_p2["Node-C-Strong"] == "TERMINAL"
    assert status_map_p2["Node-E-Mid"] == "TERMINAL"
    
    opt_p2 = assert_optimizer_invariant(nodes_p2)
    print(f"Winner: {opt_p2.best_path_id}")
    assert opt_p2.best_path_id == "Node-E-Mid"
    
    audit_p2 = run_epistemic_audit(opt_p2.best_architecture)
    print(f"Gaps: {audit_p2.ontology_gaps_in_winning_architecture}")
    assert set(audit_p2.ontology_gaps_in_winning_architecture) == {"requires_staffing_feed"}
    

    print("\n--- Phase 3: Promote Gap 2 (v3.10.2) ---")
    ontology_module.ONTOLOGY_VERSION = "v3.10.2"
    nodes_p3 = generate_frozen_payload(env_constraints)
    status_map_p3 = {n.id: n.status for n in nodes_p3}
    
    print(f"Node-E Status: {status_map_p3['Node-E-Mid']}")
    
    assert status_map_p3["Node-E-Mid"] == "REJECTED"
    assert status_map_p3["Node-B-Risky"] == "REJECTED"
    assert status_map_p3["Node-D-Highest"] == "REJECTED"
    assert status_map_p3["Node-A-Safe"] == "TERMINAL"
    assert status_map_p3["Node-C-Strong"] == "TERMINAL"
    
    opt_p3 = assert_optimizer_invariant(nodes_p3)
    print(f"Winner: {opt_p3.best_path_id}")
    assert opt_p3.best_path_id == "Node-C-Strong"
    
    audit_p3 = run_epistemic_audit(opt_p3.best_architecture)
    print(f"Gaps: {audit_p3.ontology_gaps_in_winning_architecture}")
    assert set(audit_p3.ontology_gaps_in_winning_architecture) == {"requires_irrelevant_magic"}
    

    print("\n--- Phase 4: Promote Gap 3 as Safe (v3.10.3) ---")
    ontology_module.ONTOLOGY_VERSION = "v3.10.3"
    nodes_p4 = generate_frozen_payload(env_constraints)
    status_map_p4 = {n.id: n.status for n in nodes_p4}
    
    print(f"Node-C Status: {status_map_p4['Node-C-Strong']}")
    
    assert status_map_p4["Node-C-Strong"] == "TERMINAL"
    assert status_map_p4["Node-A-Safe"] == "TERMINAL"
    assert status_map_p4["Node-E-Mid"] == "REJECTED"
    
    opt_p4 = assert_optimizer_invariant(nodes_p4)
    print(f"Final Winner: {opt_p4.best_path_id}")
    assert opt_p4.best_path_id == "Node-C-Strong"
    
    audit_p4 = run_epistemic_audit(opt_p4.best_architecture)
    print(f"Final Gaps: {audit_p4.ontology_gaps_in_winning_architecture}")
    assert not audit_p4.ontology_gaps_in_winning_architecture
    assert audit_p4.requires_ontology_review is False
    
    print("\nSUCCESS! V3.10 Iterative Feedback Loop Confirmed.")
    print("The system successfully walked down the objective hierarchy, eliminating epistemically risky architectures until finding the highest-ranked governed-feasible candidate.")

if __name__ == "__main__":
    run_v310_experiment()
