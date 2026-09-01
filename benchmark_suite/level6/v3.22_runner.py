import os
import sys
import copy

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import PathNode, optimize_tree
from decision_engine.tree.context import DecisionContext
from decision_engine.api.recommendation import generate_recommendation
from decision_engine.governance.robustness import FutureScenario
from decision_engine.input_layer.ontology import get_known_dependencies

def create_mock_arch(deps, unresolved=False):
    actual_deps = list(deps)
    if unresolved:
        actual_deps.append("unresolved_dependency_x")
        
    return ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=[], constraints=[],
        semantic_dependencies=actual_deps,
        evidence_provenance=[],
        architectural_decisions={}
    )

def print_test_header(title):
    print(f"\n==================================================")
    print(f" {title}")
    print(f"==================================================")

def run_v322_experiment():
    print("==================================================")
    print(" V3.22: MULTI-OBJECTIVE GOVERNANCE & PARETO")
    print("==================================================")
    
    base_env = [
        "emr_direct_access_authorized",
        "staffing_feed_v3_available",
        "rfid_infrastructure_v3_available"
    ]
    
    def make_env(missing):
        return [e for e in base_env if e not in missing]
        
    scenarios = [
        {"id": "S1", "family_id": "F1", "environment_constraints": make_env(["emr_direct_access_authorized"]), "probability": 0.5, "impact": 10},
        {"id": "S2", "family_id": "F2", "environment_constraints": make_env(["staffing_feed_v3_available"]), "probability": 0.5, "impact": 5},
    ]
    fs_scenarios = [FutureScenario(**s) for s in scenarios]
    
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
        future_scenarios=scenarios
    )
    
    
    cand_a = PathNode(
        id="Cand_A_HighPerf", parent_id="root",
        architecture=create_mock_arch(["requires_emr_database_integration", "requires_staffing_feed_v3"]),
        status="TERMINAL", path_score=100.0, path_cost=50.0, operational_complexity=5.0
    )
    cand_b = PathNode(
        id="Cand_B_HighRob", parent_id="root",
        architecture=create_mock_arch([]),
        status="TERMINAL", path_score=80.0, path_cost=50.0, operational_complexity=5.0
    )
    cand_c = PathNode(
        id="Cand_C_LowCost", parent_id="root",
        architecture=create_mock_arch([]),
        status="TERMINAL", path_score=70.0, path_cost=10.0, operational_complexity=5.0
    )
    cand_d = PathNode(
        id="Cand_D_Dominated", parent_id="root",
        architecture=create_mock_arch([]),
        status="TERMINAL", path_score=70.0, path_cost=15.0, operational_complexity=5.0
    )
    
    candidates = [cand_a, cand_b, cand_c, cand_d]
    
    print_test_header("TEST 1 & 2: Pareto Dominance and True Trade-off")
    res_base = optimize_tree(candidates, ctx)
    
    print(f"Pareto Frontier: {res_base.pareto_frontier}")
    assert "Cand_D_Dominated" not in res_base.pareto_frontier, "Dominated candidate MUST NOT be on the Pareto frontier."
    assert "Cand_A_HighPerf" in res_base.pareto_frontier, "Trade-off candidate A must be on the frontier."
    assert "Cand_B_HighRob" in res_base.pareto_frontier, "Trade-off candidate B must be on the frontier."
    assert "Cand_C_LowCost" in res_base.pareto_frontier, "Trade-off candidate C must be on the frontier."
    
    print_test_header("TEST 3 & 4: Weight Sensitivity & Pareto Invariance")
    ctx.optimizer_preferences["cost_lambda"] = 100.0
    res_sweep1 = optimize_tree(candidates, ctx)
    print(f"High Cost Lambda -> Winner: {res_sweep1.best_path_id} (Score: {res_sweep1.effective_score})")
    assert res_sweep1.best_path_id == "Cand_C_LowCost"
    assert abs(res_sweep1.effective_score - (-925.0)) < 1e-6
    assert res_sweep1.pareto_frontier == res_base.pareto_frontier, "Pareto frontier MUST remain invariant under weight changes!"
    
    ctx.optimizer_preferences["cost_lambda"] = 0.0
    ctx.optimizer_preferences["robustness_lambda"] = 100.0
    res_sweep2 = optimize_tree(candidates, ctx)
    print(f"High Robustness Lambda -> Winner: {res_sweep2.best_path_id} (Score: {res_sweep2.effective_score})")
    assert res_sweep2.best_path_id == "Cand_B_HighRob"
    assert abs(res_sweep2.effective_score - 175.0) < 1e-6
    assert res_sweep2.pareto_frontier == res_base.pareto_frontier, "Pareto frontier MUST remain invariant under weight changes!"
    
    print_test_header("TEST 5, 7, 8: Nasty All-Objective Unresolved Attack")
    cand_nasty = PathNode(
        id="Cand_Nasty_Unresolved", parent_id="root",
        architecture=create_mock_arch([], unresolved=True),
        status="UNRESOLVED",
        path_score=200.0,
        path_cost=0.0,
        operational_complexity=0.0
    )
    
    cand_clean = PathNode(
        id="Cand_Clean_Governed", parent_id="root",
        architecture=create_mock_arch(["requires_emr_database_integration"]),
        status="TERMINAL",
        path_score=100.0, path_cost=20.0, operational_complexity=5.0
    )
    
    ctx.optimizer_preferences = {
        "epistemic_lambda": 10.0,
        "robustness_lambda": 10.0,
        "cost_lambda": 1.0,
        "complexity_lambda": 1.0,
        "robustness_strategy": "raw"
    }
    
    res_nasty = optimize_tree([cand_nasty, cand_clean], ctx)
    print(f"Pareto Frontier: {res_nasty.pareto_frontier}")
    assert res_nasty.pareto_frontier == ["Cand_Nasty_Unresolved"], "Nasty should be the sole Pareto candidate"
    assert res_nasty.best_path_id == "Cand_Nasty_Unresolved"
    assert res_nasty.status == "UNRESOLVED", "Status must remain UNRESOLVED"
    
    recom = generate_recommendation(res_nasty.model_dump_json(), ctx)
    print(f"Action: {recom.action}")
    assert recom.action == "HOLD_FOR_REVIEW", "Action must be HOLD_FOR_REVIEW despite Pareto dominance"
    
    print_test_header("TEST 6: Robustness Duplication Resistance")
    dup_scenarios = copy.deepcopy(scenarios)
    dup_s1 = copy.deepcopy(dup_scenarios[0])
    dup_s1["id"] = "S1_Dup"
    dup_scenarios.append(dup_s1)
    
    ctx.future_scenarios = dup_scenarios
    res_dup = optimize_tree(candidates, ctx)
    assert res_dup.pareto_frontier == res_base.pareto_frontier, "Duplication should not alter Pareto frontier"
    assert res_dup.context_fingerprint != res_base.context_fingerprint, "Different scenario representation MUST alter context fingerprint"
    print("Pareto frontier invariant under scenario duplication.")
    print("Context fingerprint correctly caught the representation drift.")
    
    print("\nALL V3.22 INVARIANTS PASSED.")

if __name__ == "__main__":
    run_v322_experiment()
