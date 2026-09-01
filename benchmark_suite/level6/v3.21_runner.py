import os
import sys
import copy
import json

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import PathNode, optimize_tree
from decision_engine.tree.context import DecisionContext
from decision_engine.api.recommendation import generate_recommendation
from decision_engine.governance.robustness import evaluate_robustness, FutureScenario
import decision_engine.input_layer.ontology as ontology_module

ontology_module.ONTOLOGY_VERSION = "v3.12"

base_env = [
    "emr_direct_access_authorized",
    "staffing_feed_v3_available",
    "rfid_infrastructure_v3_available",
    "neural_link_available",
    "realtime_operational_feed_available"
]

def make_env(missing):
    return [e for e in base_env if e not in missing]

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

def run_v321_experiment():
    print("==================================================")
    print(" V3.21: CORRELATED ENVIRONMENTAL SCENARIOS")
    print("==================================================")

    cand_a = PathNode(
        id="Cand_A", parent_id="root",
        architecture=create_mock_arch(["requires_emr_database_integration"]),
        status="TERMINAL", path_cost=100.0, path_score=100.0, reject_reasons=[], epistemic_provenance=None
    )
    
    cand_b = PathNode(
        id="Cand_B", parent_id="root",
        architecture=create_mock_arch(["requires_rfid_tracking_v3"]),
        status="TERMINAL", path_cost=100.0, path_score=94.0, reject_reasons=[], epistemic_provenance=None
    )
    
    cand_c = PathNode(
        id="Cand_C", parent_id="root",
        architecture=create_mock_arch([]),
        status="TERMINAL", path_cost=100.0, path_score=91.0, reject_reasons=[], epistemic_provenance=None
    )
    
    scenarios = [
        {"id": "A1", "family_id": "Family_A", "environment_constraints": make_env(["emr_direct_access_authorized"]), "probability": 0.05, "impact": 10},
        {"id": "A2", "family_id": "Family_A", "environment_constraints": make_env(["emr_direct_access_authorized", "neural_link_available"]), "probability": 0.02, "impact": 10},
        {"id": "A3", "family_id": "Family_A", "environment_constraints": make_env(["emr_direct_access_authorized", "realtime_operational_feed_available"]), "probability": 0.03, "impact": 10},
        {"id": "B1", "family_id": "Family_B", "environment_constraints": make_env(["staffing_feed_v3_available"]), "probability": 0.30, "impact": 3},
        {"id": "B2", "family_id": "Family_B", "environment_constraints": make_env(["staffing_feed_v3_available", "neural_link_available"]), "probability": 0.15, "impact": 3},
        {"id": "B3", "family_id": "Family_B", "environment_constraints": make_env(["staffing_feed_v3_available", "realtime_operational_feed_available"]), "probability": 0.15, "impact": 3},
        {"id": "C1", "family_id": "Family_C", "environment_constraints": make_env(["rfid_infrastructure_v3_available"]), "probability": 0.15, "impact": 5},
        {"id": "C2", "family_id": "Family_C", "environment_constraints": make_env(["rfid_infrastructure_v3_available", "neural_link_available"]), "probability": 0.15, "impact": 5},
    ]

    sum_p = sum(s["probability"] for s in scenarios)
    assert abs(sum_p - 1.0) < 1e-6, "Probabilities must sum to 1"

    from decision_engine.input_layer.ontology import get_known_dependencies
    known = get_known_dependencies()
    
    print_test_header("TEST 1 & 2: Raw vs Family Survival")
    fs_scenarios = [FutureScenario(**s) for s in scenarios]
    prof_a = evaluate_robustness(cand_a, fs_scenarios, known)
    prof_b = evaluate_robustness(cand_b, fs_scenarios, known)
    
    print(f"Cand A - Raw Survival: {prof_a.survival_rate:.3f} | Family Survival: {prof_a.family_worst_case_survival:.3f}")
    print(f"Cand B - Raw Survival: {prof_b.survival_rate:.3f} | Family Survival: {prof_b.family_worst_case_survival:.3f}")
    
    assert abs(prof_a.survival_rate - 0.625) < 1e-6
    assert abs(prof_a.family_worst_case_survival - 0.6666666666666666) < 1e-6
    assert abs(prof_b.survival_rate - 0.750) < 1e-6
    assert abs(prof_b.family_worst_case_survival - 0.6666666666666666) < 1e-6
    
    print_test_header("TEST 3: Scenario Duplication Attack")
    duplicated_scenarios = copy.deepcopy(scenarios)
    duplicated_scenarios[0]["probability"] = 0.025
    dup_s1 = copy.deepcopy(duplicated_scenarios[0])
    dup_s1["id"] = "A1_prime"
    
    duplicated_scenarios[1]["probability"] = 0.01
    dup_s2 = copy.deepcopy(duplicated_scenarios[1])
    dup_s2["id"] = "A2_prime"
    
    duplicated_scenarios.extend([dup_s1, dup_s2])
    
    sum_dup_p = sum(s["probability"] for s in duplicated_scenarios)
    assert abs(sum_dup_p - 1.0) < 1e-6, "Duplicated probabilities must still sum to 1"
    
    prof_a_dup = evaluate_robustness(cand_a, [FutureScenario(**s) for s in duplicated_scenarios], known)
    print(f"Cand A (Duplicated) - Family Survival: {prof_a_dup.family_worst_case_survival:.3f} | Expected Loss: {prof_a_dup.expected_robustness_loss:.3f}")
    assert abs(prof_a.family_worst_case_survival - prof_a_dup.family_worst_case_survival) < 1e-6, "Deduplication failed!"
    assert abs(prof_a.expected_robustness_loss - prof_a_dup.expected_robustness_loss) < 1e-6, "Deduplication probability normalization failed!"
    print("Deduplication resistance verified.")
    
    malformed_scenarios = [
        {"id": "M1", "family_id": "F1", "environment_constraints": make_env(["emr_direct_access_authorized"]), "probability": 0.2, "impact": 10},
        {"id": "M2", "family_id": "F1", "environment_constraints": make_env(["staffing_feed_v3_available"]), "probability": 0.2, "impact": 5},
    ]
    prof_malformed = evaluate_robustness(cand_a, [FutureScenario(**s) for s in malformed_scenarios], known)
    assert abs(prof_malformed.expected_robustness_loss - 5.0) < 1e-6, "evaluate_robustness must normalize probabilities inherently"
    print("Probability distribution normalization invariant verified inside evaluate_robustness().")
    
    print_test_header("TEST 4: Expected Robustness Loss (Observational)")
    print(f"Cand A (Survival {prof_a.survival_rate:.2f}) -> Expected Loss: {prof_a.expected_robustness_loss:.2f}")
    print(f"Cand B (Survival {prof_b.survival_rate:.2f}) -> Expected Loss: {prof_b.expected_robustness_loss:.2f}")
    
    assert prof_a.survival_rate < prof_b.survival_rate
    assert prof_a.expected_robustness_loss < prof_b.expected_robustness_loss
    
    print_test_header("TEST 5: Robustness Preference Boundary")
    candidates = [cand_a, cand_b, cand_c]
    
    ctx = DecisionContext(
        ontology_version="v3.12", registry_policy_hashes=[],
        environment_constraints=base_env,
        optimizer_preferences={"epistemic_lambda": 0.0, "robustness_lambda": 0.0},
        future_scenarios=scenarios
    )
    
    res_base = optimize_tree(candidates, ctx)
    print(f"Lambda 0 (Base) -> Winner: {res_base.best_path_id}")
    assert res_base.best_path_id == "Cand_A"
    assert res_base.effective_score == 100.0
    
    ctx.optimizer_preferences["robustness_lambda"] = 20.0
    ctx.optimizer_preferences["robustness_strategy"] = "raw"
    res_raw = optimize_tree(candidates, ctx)
    print(f"Lambda 20 (Raw) -> Winner: {res_raw.best_path_id} (Score: {res_raw.effective_score})")
    assert res_raw.best_path_id == "Cand_A"
    assert abs(res_raw.effective_score - 112.5) < 1e-6
    
    ctx.optimizer_preferences["robustness_strategy"] = "weighted"
    res_weight = optimize_tree(candidates, ctx)
    print(f"Lambda 20 (Weighted) -> Winner: {res_weight.best_path_id} (Expected Loss: {res_weight.expected_robustness_loss}, Score: {res_weight.effective_score})")
    assert res_weight.best_path_id == "Cand_C"
    assert abs(res_weight.effective_score - 91.0) < 1e-6
    
    assert res_raw.best_path_id != res_weight.best_path_id, "Strategy change did not produce expected decision boundary crossing!"
    
    print_test_header("TEST 6: Robustness Laundering (Epistemic Integrity)")
    cand_a_nasty = PathNode(
        id="Cand_A_Nasty", parent_id="root",
        architecture=create_mock_arch([], unresolved=True),
        status="UNRESOLVED", path_cost=100.0, path_score=100.0, reject_reasons=[], epistemic_provenance=None
    )
    cand_b_clean = PathNode(
        id="Cand_B_Clean", parent_id="root",
        architecture=create_mock_arch(["requires_rfid_tracking_v3"]),
        status="TERMINAL", path_cost=100.0, path_score=90.0, reject_reasons=[], epistemic_provenance=None
    )
    
    ctx_nasty = DecisionContext(
        ontology_version="v3.12", registry_policy_hashes=[],
        environment_constraints=base_env,
        optimizer_preferences={
            "epistemic_lambda": 0.0, 
            "robustness_lambda": 1000.0,
            "robustness_strategy": "raw"
        },
        future_scenarios=scenarios
    )
    
    res_nasty = optimize_tree([cand_a_nasty, cand_b_clean], ctx_nasty)
    print(f"Nasty Winner: {res_nasty.best_path_id} | Status: {res_nasty.status}")
    
    prof_a_n = evaluate_robustness(cand_a_nasty, [FutureScenario(**s) for s in scenarios], get_known_dependencies())
    prof_b_c = evaluate_robustness(cand_b_clean, [FutureScenario(**s) for s in scenarios], get_known_dependencies())
    print(f"Cand A Nasty - Surv: {prof_a_n.survival_rate}, Raw: {cand_a_nasty.path_score}")
    print(f"Cand B Clean - Surv: {prof_b_c.survival_rate}, Raw: {cand_b_clean.path_score}")
    
    assert res_nasty.best_path_id == "Cand_A_Nasty"
    assert res_nasty.status == "UNRESOLVED", "Robustness MUST NOT silently promote to TERMINAL!"
    
    recom = generate_recommendation(res_nasty.model_dump_json(), ctx_nasty)
    print(f"Action: {recom.action}")
    assert recom.action == "HOLD_FOR_REVIEW"
    print("Robustness laundering prevented successfully.")
    
    print("\nINVARIANT CONFIRMED: Robust != Governed.")
    print("Robustness indicates environmental survivability, not epistemic trustworthiness.")
    print("A candidate with high robustness but an UNRESOLVED dependency cannot authorize action.")
    
    print("\nALL V3.21 INVARIANTS PASSED.")

if __name__ == "__main__":
    run_v321_experiment()
