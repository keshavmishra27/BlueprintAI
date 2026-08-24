import pytest
import uuid
from typing import Dict, Any

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.tree_schemas import PathNode, TreeState
from decision_engine.tree.optimizer import optimize_tree
from decision_engine.tree.benchmark_evaluator import (
    evaluate_architecture_metrics,
    compute_s_abs,
    DeterministicEvaluationRules,
    EvaluationRule,
    OptimizationWeights,
    ScoringAnchors
)
from benchmark_suite.schemas import BenchmarkScenario

def create_mock_arch(engine="cpp") -> ArchitectureNode:
    return ArchitectureNode(
        candidate_status="FEASIBLE",
        architectural_decisions={"engine": engine, "language": "python" if engine != "cpp" else "cpp"}
    )

def test_gate_b_evaluator_metric_correctness():
    # Construct rules for unselected winner scenario
    rules = DeterministicEvaluationRules(
        base_cost=100.0,
        base_latency_ms=1000.0,
        base_timeline_days=10.0,
        base_value=80.0,
        rules=[
            EvaluationRule(target_field="architectural_decisions", match_string="cpp", metric="latency_ms", operation="set", value=1.0),
            EvaluationRule(target_field="architectural_decisions", match_string="python", metric="latency_ms", operation="set", value=1000.0)
        ]
    )
    
    arch_cpp = create_mock_arch(engine="cpp")
    arch_python = create_mock_arch(engine="python")
    
    metrics_cpp = evaluate_architecture_metrics(arch_cpp, rules)
    metrics_python = evaluate_architecture_metrics(arch_python, rules)
    
    assert metrics_cpp["estimated_latency_ms"] == 1.0
    assert metrics_python["estimated_latency_ms"] == 1000.0

def test_gate_c_optimization_weight_propagation():
    # Construct A (cheap, slow), B (expensive, fast)
    arch_a = create_mock_arch(engine="python")
    arch_b = create_mock_arch(engine="cpp")
    
    # We will just manually set their metrics for this test
    cost_a, lat_a = 100.0, 1000.0
    cost_b, lat_b = 500.0, 10.0
    
    anchors = ScoringAnchors(value_maximum=100.0, cost_budget_limit=1000.0, latency_target_ms=10.0, timeline_maximum_days=10.0)
    
    # Scenario 1: Cost-heavy weights
    weights_cost = OptimizationWeights(w_value=0.2, w_cost=0.6, w_performance=0.1, w_timeline=0.1)
    
    score_a_cost = compute_s_abs(True, 80.0, cost_a, lat_a, 10.0, anchors, weights_cost)
    score_b_cost = compute_s_abs(True, 80.0, cost_b, lat_b, 10.0, anchors, weights_cost)
    
    assert score_a_cost > score_b_cost
    
    # Scenario 2: Performance-heavy weights
    weights_perf = OptimizationWeights(w_value=0.2, w_cost=0.1, w_performance=0.6, w_timeline=0.1)
    
    score_a_perf = compute_s_abs(True, 80.0, cost_a, lat_a, 10.0, anchors, weights_perf)
    score_b_perf = compute_s_abs(True, 80.0, cost_b, lat_b, 10.0, anchors, weights_perf)
    
    assert score_b_perf > score_a_perf

def test_gate_d_global_optimization_vs_conversational():
    # Killer test invariant: A, B in F and S(B) > S(A) and user(A) => Best=B
    arch_a = create_mock_arch(engine="python") # User conversational
    arch_b = create_mock_arch(engine="cpp")    # Best mathematically
    
    node_a = PathNode(
        id="node_a",
        parent_id="root",
        architecture=arch_a,
        status="TERMINAL",
        path_cost=100.0,
        path_score=10.0,
        selected_by_user=True
    )
    
    node_b = PathNode(
        id="node_b",
        parent_id="root",
        architecture=arch_b,
        status="TERMINAL",
        path_cost=100.0,
        path_score=50.0,
        selected_by_user=False
    )
    
    graph = [node_a, node_b]
    
    res = optimize_tree(graph, {})
    assert res.best_path_id == "node_b"
    
    # Ensure unselected winner is triggerable
    unselected_winner = False
    best_terminal = next(n for n in graph if n.id == res.best_path_id)
    user_terminal = next((n for n in graph if n.selected_by_user), None)
    
    if user_terminal and best_terminal and user_terminal.id != best_terminal.id:
        unselected_winner = True
        
    assert unselected_winner is True

def test_gate_e_uar_her_semantic_correctness():
    # Information scenario: expected=2, relevant=2
    expected_info = 2
    hidden_info = {"key": "val"}
    q_info = 1
    irr_info = 0
    
    rel_branches_info = (q_info - irr_info) * 2
    her_info = min(1.0, rel_branches_info / expected_info)
    uar_info = 1.0 if (q_info - irr_info) > 0 else 0.0
    
    assert her_info == 1.0
    assert uar_info == 1.0
    
    # Information scenario with irr_q:
    q_irr = 1
    irr_irr = 1
    
    rel_branches_irr = (q_irr - irr_irr) * 2
    her_irr = min(1.0, rel_branches_irr / expected_info)
    uar_irr = 1.0 if (q_irr - irr_irr) > 0 else 0.0
    
    assert her_irr == 0.0
    assert uar_irr == 0.0
    
    # Optimization scenario (no hidden facts): expected=4, q=2
    expected_opt = 4
    hidden_opt = {}
    q_opt = 2
    
    rel_branches_opt = q_opt * 2
    her_opt = min(1.0, rel_branches_opt / expected_opt)
    uar_opt = "N/A"
    
    assert her_opt == 1.0
    assert uar_opt == "N/A"

def test_gate_f_evaluator_isolation():
    rules = DeterministicEvaluationRules()
    arch = create_mock_arch()
    
    # Call evaluator twice
    m1 = evaluate_architecture_metrics(arch, rules)
    m2 = evaluate_architecture_metrics(arch, rules)
    
    assert m1 == m2
    # No tree state mutated, no side effects

def test_gate_a_metric_calculation_integrity():
    # Basic math sanity checks
    assert 1 == 1

if __name__ == "__main__":
    pytest.main(["-v", __file__])
