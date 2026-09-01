import os
import sys
import copy
import json
from pathlib import Path

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import PathNode, optimize_tree, OptimizationResult
from decision_engine.tree.context import DecisionContext
from decision_engine.api.recommendation import generate_recommendation
from decision_engine.governance.robustness import evaluate_robustness, FutureScenario
import decision_engine.input_layer.ontology as ontology_module

ontology_module.ONTOLOGY_VERSION = "v3.12"

def create_mock_arch(constraints):
    deps = []
    if "emr_direct_access_authorized" in constraints:
        deps.append("requires_emr_database_integration")
    if "rfid_infrastructure_v3_available" in constraints:
        deps.append("requires_rfid_tracking_v3")
    if "staffing_feed_v3_available" in constraints:
        deps.append("requires_staffing_feed_v3")
        
    return ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=[], constraints=[],
        semantic_dependencies=deps,
        evidence_provenance=[],
        architectural_decisions={}
    )

def print_test_header(title):
    print(f"\n==================================================")
    print(f" {title}")
    print(f"==================================================")

def run_v320_experiment():
    print("==================================================")
    print(" V3.20: ENVIRONMENT DRIFT & ROBUST ARCHITECTURE")
    print("==================================================")
    
    cand_a = PathNode(
        id="Cand_A", parent_id="root",
        architecture=create_mock_arch(["emr_direct_access_authorized", "rfid_infrastructure_v3_available", "staffing_feed_v3_available"]),
        status="TERMINAL", path_cost=100.0, path_score=100.0, reject_reasons=[], epistemic_provenance=None
    )
    
    cand_b = PathNode(
        id="Cand_B", parent_id="root",
        architecture=create_mock_arch(["emr_direct_access_authorized"]),
        status="TERMINAL", path_cost=100.0, path_score=94.0, reject_reasons=[], epistemic_provenance=None
    )
    
    scenarios = [
        {"id": "S1", "environment_constraints": ["emr_direct_access_authorized", "rfid_infrastructure_v3_available", "staffing_feed_v3_available"]},
        {"id": "S2", "environment_constraints": ["emr_direct_access_authorized", "staffing_feed_v3_available"]},
        {"id": "S3", "environment_constraints": ["emr_direct_access_authorized", "rfid_infrastructure_v3_available"]},
        {"id": "S4", "environment_constraints": ["emr_direct_access_authorized"]},
        {"id": "S5", "environment_constraints": ["emr_direct_access_authorized"]},
        {"id": "S6", "environment_constraints": ["emr_direct_access_authorized", "staffing_feed_v3_available"]},
        {"id": "S7", "environment_constraints": ["emr_direct_access_authorized", "rfid_infrastructure_v3_available"]},
        {"id": "S8", "environment_constraints": ["emr_direct_access_authorized"]},
        {"id": "S9", "environment_constraints": ["emr_direct_access_authorized"]},
        {"id": "S10", "environment_constraints": ["emr_direct_access_authorized"]}
    ]
    
    ctx_base_no_scenarios = DecisionContext(
        ontology_version="v3.12", registry_policy_hashes=[],
        environment_constraints=["emr_direct_access_authorized", "rfid_infrastructure_v3_available", "staffing_feed_v3_available"],
        optimizer_preferences={"epistemic_lambda": 0.0, "robustness_lambda": 0.0}
    )
    
    ctx_base_with_scenarios = DecisionContext(
        ontology_version="v3.12", registry_policy_hashes=[],
        environment_constraints=["emr_direct_access_authorized", "rfid_infrastructure_v3_available", "staffing_feed_v3_available"],
        optimizer_preferences={"epistemic_lambda": 0.0, "robustness_lambda": 0.0},
        future_scenarios=scenarios
    )
    
    candidates = [cand_a, cand_b]

    print_test_header("GATE 1: Audit Neutrality")
    opt_no_audit = optimize_tree(candidates, ctx_base_no_scenarios)
    opt_with_audit = optimize_tree(candidates, ctx_base_with_scenarios)
    
    print(f"No Audit Winner: {opt_no_audit.best_path_id} (Score: {opt_no_audit.effective_score})")
    print(f"With Audit Winner: {opt_with_audit.best_path_id} (Score: {opt_with_audit.effective_score})")
    
    is_neutral = (
        opt_no_audit.best_path_id == opt_with_audit.best_path_id and
        opt_no_audit.effective_score == opt_with_audit.effective_score and
        opt_no_audit.status == opt_with_audit.status
    )
    print(f"Neutrality Maintained: {is_neutral}")
    
    print_test_header("GATE 2: Robustness Determinism")
    scenarios_reversed = scenarios[::-1]
    ctx_reversed = copy.deepcopy(ctx_base_with_scenarios)
    ctx_reversed.future_scenarios = scenarios_reversed
    
    from decision_engine.input_layer.ontology import get_known_dependencies
    known = get_known_dependencies()
    p_fwd = evaluate_robustness(cand_a, [FutureScenario(**s) for s in scenarios], known)
    p_rev = evaluate_robustness(cand_a, [FutureScenario(**s) for s in scenarios_reversed], known)
    
    print(f"A Survival Fwd: {p_fwd.survival_rate} | Rev: {p_rev.survival_rate}")
    print(f"Profiles match exactly: {p_fwd.model_dump() == p_rev.model_dump()}")
    
    print_test_header("THRESHOLD SWEEP")
    lambdas_to_test = [0.0, 5.0, 6.666, 6.666666666666667, 7.0, 10.0]
    
    for lbd in lambdas_to_test:
        ctx = copy.deepcopy(ctx_base_with_scenarios)
        ctx.optimizer_preferences["robustness_lambda"] = lbd
        res = optimize_tree(candidates, ctx)
        print(f"Lambda {lbd:>18.15f} | Winner: {res.best_path_id} | Effective Score: {res.effective_score}")
        if lbd == 10.0:
            robust_result = res
            robust_ctx = ctx

    print_test_header("TEMPORAL INVARIANT CONTROL")
    mutated_ctx = copy.deepcopy(robust_ctx)
    mutated_ctx.environment_constraints = ["emr_direct_access_authorized", "staffing_feed_v3_available"]
    
    recom = generate_recommendation(robust_result.model_dump_json(), mutated_ctx)
    print(f"Recommendation Action: {recom.action} | Reason: {recom.epistemic_warnings}")

if __name__ == "__main__":
    run_v320_experiment()
