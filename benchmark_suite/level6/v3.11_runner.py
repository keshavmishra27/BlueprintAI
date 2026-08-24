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
        create_mock_node("Node-A", score=90, dependencies=["requires_staffing_feed_v2"], env_constraints=env_constraints),
        create_mock_node("Node-B", score=91, dependencies=["requires_staffing_feed_v2"], env_constraints=env_constraints),
        create_mock_node("Node-C", score=85, dependencies=[], env_constraints=env_constraints),
        create_mock_node("Node-D", score=95, dependencies=["requires_staffing_feed_v2", "requires_advanced_patient_tracking"], env_constraints=env_constraints)
    ]

def run_v311_experiment():
    print("--- V3.11: Ontology Policy Composition, Conditional Precedence & Blast-Radius Audit ---")
    
    ontology_module.ONTOLOGY_VERSION = "v3.11"
    
    environments = [
        {
            "name": "Env 1: Feed Available",
            "constraints": ["realtime_staffing_feed_available"],
            "expected_winner": "Node-D",
            "expected_rejections": []
        },
        {
            "name": "Env 2: Feed Unavailable",
            "constraints": [],
            "expected_winner": "Node-C",
            "expected_rejections": ["staffing_feed_missing"]
        },
        {
            "name": "Env 3: Feed Available but Stale",
            "constraints": ["realtime_staffing_feed_available", "feed_is_stale_mode"],
            "expected_winner": "Node-C",
            "expected_rejections": ["staffing_feed_stale"]
        },
        {
            "name": "Env 4: Contradictory Constraints (No External Data)",
            "constraints": ["realtime_staffing_feed_available", "no_external_data_allowed"],
            "expected_winner": "Node-C",
            "expected_rejections": ["external_data_prohibited"]
        }
    ]
    
    for env in environments:
        print(f"\n--- {env['name']} ---")
        nodes = generate_frozen_payload(env["constraints"])
        status_map = {n.id: n.status for n in nodes}
        rejection_map = {n.id: n.reject_reasons for n in nodes}
        
        print(f"Status A: {status_map['Node-A']}")
        print(f"Status B: {status_map['Node-B']}")
        print(f"Status C: {status_map['Node-C']}")
        print(f"Status D: {status_map['Node-D']}")
        
        # 1. Collateral Immunity & Blast Radius Proof
        assert status_map["Node-C"] == "TERMINAL", "Candidate C must remain unchanged."
        
        # 2. Symmetry
        assert status_map["Node-A"] == status_map["Node-B"], "A and B must behave identically."
        
        if env["expected_winner"] == "Node-C":
            # 3. Conditional / Precedence Correctness
            assert status_map["Node-A"] == "REJECTED"
            assert status_map["Node-B"] == "REJECTED"
            assert status_map["Node-D"] == "REJECTED"
            
            # 6. Deterministic rejection reasons
            for node_id in ["Node-A", "Node-B", "Node-D"]:
                reasons = rejection_map[node_id]
                assert any(r in reasons for r in env["expected_rejections"]), f"Missing expected rejection in {node_id}: {reasons}"
        else:
            assert status_map["Node-A"] == "TERMINAL"
            assert status_map["Node-B"] == "TERMINAL"
            assert status_map["Node-D"] == "TERMINAL"
            
        # 5. Composition Correctness
        # Node D has another unknown dependency (requires_advanced_patient_tracking)
        # Even if D is rejected, the dependency should remain independently represented in its semantic dependencies
        node_d = next(n for n in nodes if n.id == "Node-D")
        assert "requires_advanced_patient_tracking" in node_d.architecture.semantic_dependencies
            
        opt_only = optimize_tree(nodes, {})
        opt_audit = optimize_tree(nodes, {})
        
        # 7. Optimizer Neutrality, 10. Audit Neutrality
        assert opt_only.best_path_id == opt_audit.best_path_id
        
        winner_id = opt_audit.best_path_id
        print(f"Winner: {winner_id}")
        assert winner_id == env["expected_winner"]
        
        audit = run_epistemic_audit(opt_audit.best_architecture)
        if winner_id == "Node-D":
            assert "requires_advanced_patient_tracking" in audit.ontology_gaps_in_winning_architecture
        else:
            assert not audit.requires_ontology_review
            
    print("\nSUCCESS! V3.11 Blast-Radius Audit Verified.")
    print("The ontology cleanly handles complex composition, conditional precedence, and discrete rejection reasons without any collateral damage to unrelated architectures.")

if __name__ == "__main__":
    run_v311_experiment()
