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

def create_mock_node(node_id: str, score: float, cost: float, dependencies: list, env_constraints: list) -> PathNode:
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
        path_cost=cost,
        path_latency=1.0,
        path_score=score,
        reject_reasons=res.constraint_failures + res.requirement_failures
    )

def run_v39_experiment():
    print("--- V3.9: Gap Promotion & Identical-Input Replay ---")
    
    env_constraints = ["budget_less_than_500_per_month"]
    
    def generate_frozen_payload():
        return [
            create_mock_node("Node-A-Safe", score=89, cost=100, dependencies=[], env_constraints=env_constraints),
            create_mock_node("Node-B-Risky", score=90, cost=100, dependencies=["requires_advanced_patient_tracking"], env_constraints=env_constraints)
        ]
        
    print("\n--- PHASE 1: PRE-PROMOTION (V3.8 STATE) ---")
    ontology_module.ONTOLOGY_VERSION = "v3.8"
    nodes_v38 = generate_frozen_payload()
    
    print(f"Candidate B Status: {nodes_v38[1].status}")
    assert nodes_v38[1].status == "TERMINAL", "Expected Candidate B to be feasible because the dependency is un-governed."
    
    opt_v38 = optimize_tree(nodes_v38, {})
    winner_v38 = opt_v38.best_architecture
    winner_id_v38 = opt_v38.best_path_id
    print(f"Optimizer Winner: {winner_id_v38}")
    
    audit_v38 = run_epistemic_audit(winner_v38)
    print(f"Audit Requires Review: {audit_v38.requires_ontology_review}")
    print(f"Gaps: {audit_v38.ontology_gaps_in_winning_architecture}")
    
    assert winner_id_v38 == "Node-B-Risky"
    assert audit_v38.requires_ontology_review is True
    
    print("\n--- PHASE 2: CURATOR PROMOTION ---")
    print("Promoting `requires_advanced_patient_tracking` to deterministic policy (requires `rfid_infrastructure_available`).")
    print("Ontology version updated to v3.9.")
    
    print("\n--- PHASE 3: POST-PROMOTION REPLAY ---")
    ontology_module.ONTOLOGY_VERSION = "v3.9"
    nodes_v39 = generate_frozen_payload()
    
    print(f"Candidate B Status: {nodes_v39[1].status}")
    if nodes_v39[1].status == 'REJECTED':
        print(f"Candidate B Rejection Reasons: {nodes_v39[1].reject_reasons}")
    
    assert nodes_v39[1].status == "REJECTED", "Candidate B should be rejected due to missing RFID infrastructure."
    
    opt_v39_only = optimize_tree(nodes_v39, {})
    
    opt_v39_then = optimize_tree(nodes_v39, {})
    winner_v39 = opt_v39_then.best_architecture
    winner_id_v39 = opt_v39_then.best_path_id
    
    assert opt_v39_only.best_path_id == opt_v39_then.best_path_id, "Audit affected optimization."
    
    print(f"Optimizer Winner: {winner_id_v39}")
    audit_v39 = run_epistemic_audit(winner_v39)
    print(f"Audit Requires Review: {audit_v39.requires_ontology_review}")
    
    assert winner_id_v39 == "Node-A-Safe", "Optimizer should fall back to A since B is rejected."
    assert audit_v39.requires_ontology_review is False, "Candidate A should have no gaps."
    
    print("\nSUCCESS! V3.9 Ontology Promotion Causal Loop Verified.")
    print("The exact same architecture that was selected in V3.8 is properly rejected in V3.9 solely due to explicitly acquired deterministic knowledge.")

if __name__ == "__main__":
    run_v39_experiment()
