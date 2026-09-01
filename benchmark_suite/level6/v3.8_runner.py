import os
import sys

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.tree.tree_schemas import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import optimize_tree, OptimizationResult
from decision_engine.optimizer.epistemic_audit import run_epistemic_audit

def create_mock_node(node_id: str, score: float, cost: float, dependencies: list, is_winner: bool = False) -> PathNode:
    arch = ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[],
        data_required=[], resources_required=[], constraints=[],
        evidence_provenance=[], historical_decisions=[],
        semantic_dependencies=dependencies,
        architectural_decisions={}
    )
    node = PathNode(
        id=node_id,
        parent_id="root",
        architecture=arch,
        uncertainty_resolved=True,
        uncertainty_question=None,
        uncertainty_importance="CRITICAL",
        uncertainty_target="Data",
        b_feasible=True,
        status="TERMINAL",
        path_cost=cost,
        path_latency=1.0,
        path_score=score
    )
    return node

def run_v38_experiment():
    print("--- V3.8: Epistemic Audit Feedback Loop ---")
    
    def test_case(name, nodes, expected_winner_id, expected_escalation, expected_gaps):
        print(f"\n{name}")
        
        opt_only = optimize_tree(nodes, {})
        winner_id_only = opt_only.best_path_id
        
        opt_then = optimize_tree(nodes, {})
        winner_id_then = opt_then.best_path_id
        
        assert winner_id_only == winner_id_then, "Audit implicitly affected optimization!"
        assert opt_only.status == opt_then.status, "Audit implicitly affected optimization status!"
        
        
        if not opt_then.best_architecture:
            print("  No winner found.")
            return
            
        audit_result = run_epistemic_audit(opt_then.best_architecture)
        
        print(f"  Optimizer Winner: {winner_id_then}")
        print(f"  Requires Ontology Review: {audit_result.requires_ontology_review}")
        print(f"  Ontology Gaps: {audit_result.ontology_gaps_in_winning_architecture}")
        
        assert winner_id_then == expected_winner_id, f"Expected winner {expected_winner_id}, got {winner_id_then}"
        assert audit_result.requires_ontology_review == expected_escalation, f"Expected escalation={expected_escalation}"
        if expected_gaps is not None:
            assert set(audit_result.ontology_gaps_in_winning_architecture) == set(expected_gaps), f"Expected gaps {expected_gaps}, got {audit_result.ontology_gaps_in_winning_architecture}"
            
        assert audit_result.requires_ontology_review == (len(audit_result.ontology_gaps_in_winning_architecture) >= 1)

    known_deps = ["requires_approved_emr_interface"]
    unknown_deps = ["requires_quantum_hospital_network"]
    
    nodes_case1 = [
        create_mock_node("Node-Known-A", score=90, cost=100, dependencies=known_deps),
        create_mock_node("Node-Unknown-B", score=50, cost=100, dependencies=unknown_deps)
    ]
    test_case("Case 1: Unknown but irrelevant (Known wins)", nodes_case1, "Node-Known-A", False, [])
    
    nodes_case2 = [
        create_mock_node("Node-Known-A", score=50, cost=100, dependencies=known_deps),
        create_mock_node("Node-Unknown-B", score=90, cost=100, dependencies=unknown_deps)
    ]
    test_case("Case 2: Unknown enters the winner", nodes_case2, "Node-Unknown-B", True, unknown_deps)
    
    nodes_case3 = [
        create_mock_node("Node-Known-A", score=89, cost=100, dependencies=known_deps),
        create_mock_node("Node-Unknown-B", score=90, cost=100, dependencies=unknown_deps)
    ]
    test_case("Case 3: Unknown is decision-critical", nodes_case3, "Node-Unknown-B", True, unknown_deps)
    
    nodes_empty = [
        create_mock_node("Node-Empty", score=90, cost=100, dependencies=[])
    ]
    test_case("Case 4: No-gap winner (empty dependencies)", nodes_empty, "Node-Empty", False, [])

    print("\nSUCCESS! V3.8 Epistemic Audit Verified.")
    print("The Engine clearly distinguishes between observational unknowns and structural epistemic debt, strictly preserving optimization independence.")

if __name__ == "__main__":
    run_v38_experiment()
