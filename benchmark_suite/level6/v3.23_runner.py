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
from decision_engine.api.recommendation import generate_recommendation

def create_mock_arch(deps):
    return ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=[], constraints=[],
        semantic_dependencies=list(deps),
        evidence_provenance=[],
        architectural_decisions={}
    )

def print_test(name, expected, actual, passed):
    print(f"{'PASS' if passed else 'FAIL'} | {name.ljust(45)} | Exp: {expected.ljust(20)} | Act: {actual}")
    if not passed:
        raise AssertionError(f"Test {name} failed: expected {expected}, got {actual}")

def run_v323_experiment():
    print("==================================================")
    print(" V3.23: DECISION GRAPH INTEGRITY")
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
    cand_c = PathNode(
        id="Cand_C", parent_id="Cand_B",
        architecture=create_mock_arch(["deps_C"]),
        status="TERMINAL", path_score=60.0, path_cost=10.0, operational_complexity=5.0
    )
    
    G0 = [cand_a, cand_b, cand_c]
    
    opt_result = optimize_tree(G0, ctx, graph_version="v1")
    serialized_opt = opt_result.model_dump_json()
    
    print(f"\nBaseline Winner: {opt_result.best_path_id} (Expected: Cand_A)\n")
    assert opt_result.best_path_id == "Cand_A"

    def eval_attack(name, mutated_graph, mutated_ctx, mutated_payload, expected_action, expected_reason=None, graph_version="v1"):
        res = generate_recommendation(mutated_payload, mutated_ctx, mutated_graph, current_graph_version=graph_version)
        passed = (res.action == expected_action)
        if expected_reason and res.epistemic_warnings:
            passed = passed and (res.epistemic_warnings.get("reason") == expected_reason)
            reason_str = res.epistemic_warnings.get("reason")
        elif expected_reason and not res.epistemic_warnings:
            passed = False
            reason_str = "None"
        else:
            reason_str = ""
            
        full_actual = f"{res.action} {reason_str}"
        full_expected = f"{expected_action} {expected_reason or ''}"
        print_test(name, full_expected, full_actual, passed)
        return res
        
    eval_attack("1. Identical graph replay", G0, ctx, serialized_opt, "RECOMMEND")
    
    cand_d = PathNode(
        id="Cand_D", parent_id="root", architecture=create_mock_arch(["deps_D"]),
        status="TERMINAL", path_score=50.0, path_cost=10.0, operational_complexity=5.0
    )
    G_add = copy.deepcopy(G0) + [cand_d]
    eval_attack("2. Candidate added", G_add, ctx, serialized_opt, "HOLD_FOR_REVIEW", "STALE_DECISION_GRAPH")
    
    G_rem = [cand_b, cand_c]
    eval_attack("3. Winner removed", G_rem, ctx, serialized_opt, "REJECT", "INVALIDATED_DECISION_ARTIFACT")
    
    G_mod_nonwin = copy.deepcopy(G0)
    G_mod_nonwin[1].architecture.semantic_dependencies = ["deps_B_mutated"]
    eval_attack("4. Non-winning arch changed", G_mod_nonwin, ctx, serialized_opt, "HOLD_FOR_REVIEW", "STALE_DECISION_GRAPH")
    
    opt_tampered = copy.deepcopy(opt_result)
    opt_tampered.best_architecture.semantic_dependencies = ["deps_A_mutated"]
    tampered_json = opt_tampered.model_dump_json()
    eval_attack("5. Winning arch payload tampered", G0, ctx, tampered_json, "REJECT", "COMPROMISED_DECISION_INTEGRITY")
    
    G_sub = copy.deepcopy(G0)
    G_sub[0].architecture.semantic_dependencies = ["deps_A_mutated"]
    eval_attack("6. Winner arch substituted in graph", G_sub, ctx, serialized_opt, "REJECT", "INVALIDATED_DECISION_ARTIFACT")
    
    G_edge = copy.deepcopy(G0)
    G_edge[2].parent_id = "Cand_A"
    eval_attack("7. Graph edge changed", G_edge, ctx, serialized_opt, "HOLD_FOR_REVIEW", "STALE_DECISION_GRAPH")
    
    G_reordered = [cand_c, cand_a, cand_b]
    eval_attack("8. Graph node reordered", G_reordered, ctx, serialized_opt, "RECOMMEND")
    
    eval_attack("9. Edge ordering changed", G_reordered, ctx, serialized_opt, "RECOMMEND")
    
    eval_attack("10. Fake graph version", G0, ctx, serialized_opt, "REJECT", "INVALIDATED_DECISION_ARTIFACT", graph_version="v2")
    
    opt_fake_fp = copy.deepcopy(opt_result)
    opt_fake_fp.graph_fingerprint = "fake123"
    fake_fp_json = opt_fake_fp.model_dump_json()
    eval_attack("11. Fake graph fingerprint (payload int.)", G0, ctx, fake_fp_json, "REJECT", "COMPROMISED_DECISION_INTEGRITY")
    
    ctx_mod = copy.deepcopy(ctx)
    ctx_mod.environment_constraints = ["new_constraint_to_change_fingerprint"]
    eval_attack("12. Graph + context both changed", G_add, ctx_mod, serialized_opt, "HOLD_FOR_REVIEW", "STALE_DECISION_GRAPH")
    
    print_test("13. Re-optimize on drifted graph", "", "", True)
    opt_new = optimize_tree(G_add, ctx, graph_version="v2")
    new_json = opt_new.model_dump_json()
    eval_attack("13. Replay new decision on new graph", G_add, ctx, new_json, "RECOMMEND", None, graph_version="v2")

    print("\nALL V3.23 INVARIANTS PASSED.")

if __name__ == "__main__":
    run_v323_experiment()
