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
        create_mock_node("Node-A", score=90, dependencies=["requires_staffing_feed_v3"], env_constraints=env_constraints),
        create_mock_node("Node-B", score=91, dependencies=["requires_rfid_tracking_v3"], env_constraints=env_constraints),
        create_mock_node("Node-C", score=95, dependencies=["requires_staffing_feed_v3", "requires_rfid_tracking_v3"], env_constraints=env_constraints),
        create_mock_node("Node-D", score=80, dependencies=[], env_constraints=env_constraints)
    ]

def run_v312_experiment():
    print("--- V3.12: Multi-Policy Interaction & Compositional Failure Audit ---")
    
    ontology_module.ONTOLOGY_VERSION = "v3.12"
    
    environments = [
        {
            "id": "env1",
            "name": "Env 1: Both Available",
            "constraints": ["staffing_feed_v3_available", "rfid_infrastructure_v3_available"],
            "expected_winner": "Node-C",
            "expected_c_rejections": set()
        },
        {
            "id": "env2",
            "name": "Env 2: Staffing Missing",
            "constraints": ["rfid_infrastructure_v3_available"],
            "expected_winner": "Node-B",
            "expected_c_rejections": {"staffing_feed_missing"}
        },
        {
            "id": "env3",
            "name": "Env 3: RFID Missing",
            "constraints": ["staffing_feed_v3_available"],
            "expected_winner": "Node-A",
            "expected_c_rejections": {"rfid_infrastructure_missing"}
        },
        {
            "id": "env4",
            "name": "Env 4: Both Missing",
            "constraints": [],
            "expected_winner": "Node-D",
            "expected_c_rejections": {"staffing_feed_missing", "rfid_infrastructure_missing"}
        }
    ]
    
    results = {}
    
    for env in environments:
        print(f"\n--- {env['name']} ---")
        nodes = generate_frozen_payload(env["constraints"])
        status_map = {n.id: n.status for n in nodes}
        rejection_map = {n.id: set(n.reject_reasons) for n in nodes}
        
        results[env["id"]] = rejection_map["Node-C"]
        
        print(f"Status A: {status_map['Node-A']}")
        print(f"Status B: {status_map['Node-B']}")
        print(f"Status C: {status_map['Node-C']}")
        print(f"Status D: {status_map['Node-D']}")
        
        if env["id"] == "env1":
            assert status_map["Node-A"] == "TERMINAL"
            assert status_map["Node-B"] == "TERMINAL"
            assert status_map["Node-C"] == "TERMINAL"
            assert status_map["Node-D"] == "TERMINAL"
        elif env["id"] == "env2":
            assert status_map["Node-A"] == "REJECTED"
            assert status_map["Node-B"] == "TERMINAL"
            assert status_map["Node-C"] == "REJECTED"
            assert status_map["Node-D"] == "TERMINAL"
        elif env["id"] == "env3":
            assert status_map["Node-A"] == "TERMINAL"
            assert status_map["Node-B"] == "REJECTED"
            assert status_map["Node-C"] == "REJECTED"
            assert status_map["Node-D"] == "TERMINAL"
        elif env["id"] == "env4":
            assert status_map["Node-A"] == "REJECTED"
            assert status_map["Node-B"] == "REJECTED"
            assert status_map["Node-C"] == "REJECTED"
            assert status_map["Node-D"] == "TERMINAL"
            
        opt = optimize_tree(nodes, {})
        print(f"Winner: {opt.best_path_id}")
        assert opt.best_path_id == env["expected_winner"]
        
        print(f"Node-C Rejections: {rejection_map['Node-C']}")
        assert rejection_map["Node-C"] == env["expected_c_rejections"], f"Expected {env['expected_c_rejections']} got {rejection_map['Node-C']}"
        
    print("\n--- Counterfactual Isolation Proof ---")
    env1_c = results["env1"]
    env2_c = results["env2"]
    env3_c = results["env3"]
    env4_c = results["env4"]
    
    print(f"Env2(C) - Env1(C) = {env2_c - env1_c}")
    print(f"Env3(C) - Env1(C) = {env3_c - env1_c}")
    print(f"Env4(C) - Env1(C) = {env4_c - env1_c}")
    
    assert (env2_c - env1_c) == {"staffing_feed_missing"}
    assert (env3_c - env1_c) == {"rfid_infrastructure_missing"}
    assert (env4_c - env1_c) == {"staffing_feed_missing", "rfid_infrastructure_missing"}
    
    print("\nSUCCESS! V3.12 Multi-Policy Interaction & Compositional Failure Audit Verified.")
    print("The evaluator flawlessly aggregates multiple independent causal failures, without short-circuiting or conflating parallel ontology rules.")

if __name__ == "__main__":
    run_v312_experiment()
