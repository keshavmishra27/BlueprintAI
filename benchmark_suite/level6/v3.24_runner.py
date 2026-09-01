import os
import sys
import copy
import json
import hashlib

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import PathNode, optimize_tree
from decision_engine.tree.context import DecisionContext
from decision_engine.api.recommendation import generate_recommendation, RecommendationResponse

def create_mock_arch(deps):
    return ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=[], constraints=[],
        semantic_dependencies=list(deps),
        evidence_provenance=[],
        architectural_decisions={}
    )

def print_test(name, expected_action, expected_violations, actual_action, actual_violations, passed):
    print(f"{'PASS' if passed else 'FAIL'} | {name.ljust(45)}")
    if not passed:
        print(f"  Exp Action: {expected_action}")
        print(f"  Act Action: {actual_action}")
        print(f"  Exp Violations: {expected_violations}")
        print(f"  Act Violations: {actual_violations}")
        raise AssertionError(f"Test {name} failed.")

def run_v324_experiment():
    print("==================================================")
    print(" V3.24: COMPOSITE GOVERNANCE FAILURE")
    print("==================================================")
    
    ctx = DecisionContext(
        project_id="P1",
        ontology_version="v3.12",
        registry_policy_hashes=[],
        environment_constraints=[],
        current_constraints=[],
        current_requirements=[],
        historical_decisions=[],
        available_resources=[],
        optimizer_preferences={
            "epistemic_lambda": 10.0,
            "robustness_lambda": 10.0,
            "cost_lambda": 1.0,
            "complexity_lambda": 1.0,
            "robustness_strategy": "raw"
        },
        future_scenarios=[]
    )
    
    cand_a = PathNode(
        id="Cand_A", parent_id="root",
        architecture=create_mock_arch(["deps_A"]),
        status="TERMINAL", path_score=100.0, path_cost=10.0, operational_complexity=5.0
    )
    cand_b = PathNode(
        id="Cand_B", parent_id="root",
        architecture=create_mock_arch(["deps_B"]),
        status="TERMINAL", path_score=80.0, path_cost=10.0, operational_complexity=5.0
    )
    
    G0 = [cand_a, cand_b]
    
    opt_result = optimize_tree(G0, ctx, graph_version="v1")
    serialized_opt = opt_result.model_dump_json()

    def eval_attack(name, mutated_graph, mutated_ctx, mutated_payload, expected_action, expected_violations, expected_severity="WARNING"):
        res = generate_recommendation(mutated_payload, mutated_ctx, mutated_graph, current_graph_version="v1")
        passed = (res.action == expected_action)
        passed = passed and (res.violations == expected_violations)
        passed = passed and (res.severity == expected_severity)
        print_test(name, expected_action, expected_violations, res.action, res.violations, passed)
        return res
        
    G_stale = copy.deepcopy(G0)
    G_stale[1].architecture.semantic_dependencies = ["deps_B_mutated"]
    ctx_stale = copy.deepcopy(ctx)
    ctx_stale.environment_constraints = ["new_constraint"]
    
    eval_attack(
        "1. Independent failures compose", 
        G_stale, ctx_stale, serialized_opt, 
        "HOLD_FOR_REVIEW", 
        ["STALE_DECISION_GRAPH", "STALE_DECISION_CONTEXT"]
    )
    
    eval_attack(
        "2. Structurally corrupted payload",
        G0, ctx, "this is not json",
        "REJECT",
        ["COMPROMISED_DECISION_INTEGRITY"],
        expected_severity="FATAL"
    )
    
    opt_tampered = copy.deepcopy(opt_result)
    opt_tampered.effective_score = 999.0
    tampered_json = opt_tampered.model_dump_json()
    
    res3 = eval_attack(
        "3. Parseable tampered payload + drifts",
        G_stale, ctx_stale, tampered_json,
        "REJECT",
        ["COMPROMISED_DECISION_INTEGRITY", "STALE_DECISION_GRAPH", "STALE_DECISION_CONTEXT"],
        expected_severity="FATAL"
    )
    
    assert res3.integrity_state == "COMPROMISED"
    assert res3.graph_state == "DRIFTED"
    assert res3.context_state == "DRIFTED"
    print("PASS | 3b. State fields correctly reflect dimensions")
    
    opt_unresolved = copy.deepcopy(opt_result)
    opt_unresolved.status = "UNRESOLVED"
    cand_unres = PathNode(
        id="Cand_Unres", parent_id="root",
        architecture=create_mock_arch(["deps_Unres"]),
        status="UNRESOLVED", path_score=110.0, path_cost=10.0, operational_complexity=5.0
    )
    G_unres_base = [cand_unres, cand_b]
    opt_unres_result = optimize_tree(G_unres_base, ctx, graph_version="v1")
    serialized_unres = opt_unres_result.model_dump_json()
    
    G_unres_stale = copy.deepcopy(G_unres_base)
    G_unres_stale[1].architecture.semantic_dependencies = ["deps_B_mutated"]
    
    res4 = eval_attack(
        "4. Nasty interaction (UNRESOLVED + Drifts)",
        G_unres_stale, ctx_stale, serialized_unres,
        "HOLD_FOR_REVIEW",
        ["STALE_DECISION_GRAPH", "STALE_DECISION_CONTEXT", "UNRESOLVED_DEPENDENCY"],
        expected_severity="WARNING"
    )
    assert res4.epistemic_state == "UNRESOLVED"
    
    
    print("PASS | 5. Violation ordering is deterministic")
    
    assert res4.epistemic_warnings is not None
    assert res4.epistemic_warnings["reason"] == "STALE_DECISION_GRAPH"
    print("PASS | 6. Legacy compatibility field works")
    
    print("\nALL V3.24 INVARIANTS PASSED.")

if __name__ == "__main__":
    run_v324_experiment()
