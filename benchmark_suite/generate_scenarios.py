import json
import sys
from pathlib import Path
import copy

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import Requirement, ArchitectureNode
from benchmark_suite.schemas import BenchmarkScenario, EvaluationRule, DeterministicEvaluationRules
from decision_engine.tree.benchmark_evaluator import ScoringAnchors, OptimizationWeights

def write_scenario(scenario: BenchmarkScenario, filename: str):
    out_path = Path(__file__).parent / "scenarios" / filename
    with open(out_path, "w") as f:
        json.dump(scenario.model_dump(), f, indent=4)
    print(f"Generated {out_path}")

def get_hospital_rules():
    return DeterministicEvaluationRules(
        base_cost=100.0,
        base_latency_ms=1000.0,
        base_timeline_days=10.0,
        base_value=80.0,
        rules=[
            EvaluationRule(target_field="architectural_decisions", match_string="cloud", metric="cost", operation="add", value=1000.0),
            EvaluationRule(target_field="architectural_decisions", match_string="aws", metric="cost", operation="add", value=1000.0),
            EvaluationRule(target_field="architectural_decisions", match_string="cloud", metric="timeline_days", operation="add", value=15.0),
            EvaluationRule(target_field="architectural_decisions", match_string="api", metric="cost", operation="add", value=50.0),
            EvaluationRule(target_field="architectural_decisions", match_string="csv", metric="latency_ms", operation="set", value=86400000.0),
            EvaluationRule(target_field="architectural_decisions", match_string="usb", metric="latency_ms", operation="set", value=86400000.0),
            EvaluationRule(target_field="architectural_decisions", match_string="manual", metric="latency_ms", operation="set", value=86400000.0),
            EvaluationRule(target_field="architectural_decisions", match_string="xgboost", metric="value", operation="set", value=95.0),
            EvaluationRule(target_field="architectural_decisions", match_string="ml model", metric="value", operation="set", value=95.0),
            EvaluationRule(target_field="architectural_decisions", match_string="moving average", metric="value", operation="set", value=60.0),
            EvaluationRule(target_field="architectural_decisions", match_string="statistical", metric="value", operation="set", value=60.0),
        ]
    )

def generate_test_optimal_baseline():
    oracle_arch = ArchitectureNode(
        inputs=["Direct database queries"],
        processing=["Lightweight cron job"],
        decision=["Rule-based engine"],
        output=["Dashboard"],
        capabilities=["daily baseline"],
        data_required=["historical data"],
        resources_required=["existing cloud instance"],
        constraints=["budget <= $1000/month", "reliable internet"],
        evidence_provenance=[],
        architectural_decisions={"compute_location": "cloud"}
    )
    
    scenario = BenchmarkScenario(
        name="Optimal Baseline",
        description="The simplest single-shot architecture is already perfect. Don't ruin it.",
        problem_what="Dashboard",
        problem_why="Need to see data",
        problem_how="Query DB",
        constraints=["budget <= $1000/month", "reliable internet"],
        requirements=[Requirement(name="fast query", required=True)],
        scoring_anchors=ScoringAnchors(value_maximum=100.0, cost_budget_limit=1000.0, latency_target_ms=100.0, timeline_maximum_days=10.0),
        optimization_weights=OptimizationWeights(w_value=0.5, w_cost=0.5, w_performance=0.0, w_timeline=0.0),
        oracle_architecture=oracle_arch,
        evaluation_rules=get_hospital_rules(),
        expected_relevant_branches=0
    )
    write_scenario(scenario, "test_optimal_baseline.json")

def generate_test_impossible():
    scenario = BenchmarkScenario(
        name="Impossible Scenario",
        description="Requires 1ms latency for $1.",
        problem_what="Realtime ML",
        problem_why="Need speed",
        problem_how="ML",
        constraints=["budget <= $1/month", "latency <= 1ms"],
        requirements=[Requirement(name="fast", required=True)],
        scoring_anchors=ScoringAnchors(value_maximum=100.0, cost_budget_limit=1.0, latency_target_ms=1.0, timeline_maximum_days=10.0),
        optimization_weights=OptimizationWeights(w_value=0.5, w_cost=0.5, w_performance=0.0, w_timeline=0.0),
        oracle_architecture=None,
        evaluation_rules=get_hospital_rules(),
        expected_relevant_branches=0
    )
    write_scenario(scenario, "test_impossible.json")

def generate_test_irrelevant_uncertainty():
    oracle_arch = ArchitectureNode(
        inputs=["Database"],
        processing=["Basic Script"],
        decision=["None"],
        output=["Blue UI Dashboard"],
        capabilities=["Show data"],
        data_required=["db records"],
        resources_required=["server"],
        constraints=["budget <= $500/month"],
        evidence_provenance=[],
        architectural_decisions={"ui_color": "blue"}
    )
    scenario = BenchmarkScenario(
        name="Irrelevant Uncertainty",
        description="Agent asks about UI color, which has zero deterministic consequence.",
        problem_what="Build a dashboard",
        problem_why="To view metrics",
        problem_how="Simple web app",
        constraints=["budget <= $500/month"],
        requirements=[Requirement(name="show metrics", required=True)],
        scoring_anchors=ScoringAnchors(value_maximum=100.0, cost_budget_limit=500.0, latency_target_ms=1000.0, timeline_maximum_days=30.0),
        optimization_weights=OptimizationWeights(w_value=0.5, w_cost=0.5, w_performance=0.0, w_timeline=0.0),
        oracle_architecture=oracle_arch,
        evaluation_rules=get_hospital_rules(),
        expected_relevant_branches=0
    )
    write_scenario(scenario, "test_irrelevant_uncertainty.json")

def generate_test_unselected_winner():
    oracle_arch = ArchitectureNode(
        inputs=["Fast API"],
        processing=["Optimized C++ Engine"],
        decision=["Advanced Rules"],
        output=["High Speed Dashboard"],
        capabilities=["Sub-millisecond processing"],
        data_required=["stream"],
        resources_required=["high end server"],
        constraints=["budget <= $5000/month"],
        evidence_provenance=[],
        architectural_decisions={"engine": "cpp"}
    )
    
    rules = get_hospital_rules()
    rules.rules.extend([
        EvaluationRule(target_field="architectural_decisions", match_string="cpp", metric="latency_ms", operation="set", value=0.001),
        EvaluationRule(target_field="architectural_decisions", match_string="c++", metric="latency_ms", operation="set", value=0.001),
        EvaluationRule(target_field="architectural_decisions", match_string="python", metric="latency_ms", operation="set", value=1.0)
    ])
    
    scenario = BenchmarkScenario(
        name="Unselected Winner",
        description="User picks Branch A, but Branch B mathematically dominates.",
        problem_what="High freq trading",
        problem_why="Profit",
        problem_how="C++ or Python",
        constraints=["budget <= $5000/month"],
        requirements=[Requirement(name="lowest possible latency", required=True)],
        scoring_anchors=ScoringAnchors(value_maximum=100.0, cost_budget_limit=5000.0, latency_target_ms=1.0, timeline_maximum_days=60.0),
        optimization_weights=OptimizationWeights(w_value=0.2, w_cost=0.1, w_performance=0.7, w_timeline=0.0),
        oracle_architecture=oracle_arch,
        evaluation_rules=rules,
        expected_relevant_branches=2
    )
    write_scenario(scenario, "test_unselected_winner.json")

def generate_test_false_confidence():
    oracle_arch = ArchitectureNode(
        inputs=["Cloud API"],
        processing=["Standard VM"],
        decision=["Basic"],
        output=["Web UI"],
        capabilities=["general purpose"],
        data_required=["basic"],
        resources_required=["standard vm"],
        constraints=["no custom hardware"],
        evidence_provenance=[],
        architectural_decisions={"compute": "standard"}
    )
    scenario = BenchmarkScenario(
        name="False Confidence",
        description="LLM claims it doesn't need custom hardware, but structure explicitly says it does.",
        problem_what="Run a specialized model",
        problem_why="Need specific results",
        problem_how="Model inference",
        constraints=["no custom hardware"],
        requirements=[Requirement(name="run model", required=True)],
        scoring_anchors=ScoringAnchors(value_maximum=100.0, cost_budget_limit=1000.0, latency_target_ms=1000.0, timeline_maximum_days=30.0),
        optimization_weights=OptimizationWeights(w_value=0.5, w_cost=0.5, w_performance=0.0, w_timeline=0.0),
        oracle_architecture=oracle_arch,
        evaluation_rules=get_hospital_rules(),
        expected_relevant_branches=0
    )
    write_scenario(scenario, "test_false_confidence.json")

def generate_test_feasible_tie():
    oracle_arch = ArchitectureNode(
        inputs=["CSV"],
        processing=["Pandas"],
        decision=["Rule"],
        output=["Report A"],
        capabilities=["Reporting"],
        data_required=["CSV"],
        resources_required=["Laptop"],
        constraints=["budget <= $100"],
        evidence_provenance=[],
        architectural_decisions={"tool": "pandas"}
    )
    scenario = BenchmarkScenario(
        name="Feasible Tie",
        description="Two completely identical scoring architectures. Tie breaker must hold.",
        problem_what="Parse CSV",
        problem_why="Reporting",
        problem_how="Pandas or Polars",
        constraints=["budget <= $100"],
        requirements=[Requirement(name="Parse data", required=True)],
        scoring_anchors=ScoringAnchors(value_maximum=100.0, cost_budget_limit=100.0, latency_target_ms=1000.0, timeline_maximum_days=10.0),
        optimization_weights=OptimizationWeights(w_value=0.5, w_cost=0.5, w_performance=0.0, w_timeline=0.0),
        oracle_architecture=oracle_arch,
        evaluation_rules=get_hospital_rules(),
        expected_relevant_branches=2
    )
    write_scenario(scenario, "test_feasible_tie.json")

def generate_test_hidden_assumption():
    oracle_arch = ArchitectureNode(
        inputs=[
            "authorized CSV export from hospital DB",
            "manual USB transfer by admin"
        ],
        processing=[
            "Local script processing CSV data daily",
            "Lightweight XGBoost model trained on historical data"
        ],
        decision=[
            "Risk threshold model predicting queue spikes 24hr in advance"
        ],
        output=[
            "Local static HTML dashboard hosted on existing machine"
        ],
        capabilities=[
            "daily wait time prediction baseline",
            "overcrowding risk alerts"
        ],
        data_required=[
            "historical queue data",
            "staffing data"
        ],
        resources_required=[
            "existing hospital computer"
        ],
        constraints=[
            "budget <= $500/month",
            "no cloud infrastructure",
            "existing hospital computers only",
            "unreliable internet",
            "30-day prototype",
            "patient data must remain local"
        ],
        evidence_provenance=[],
        architectural_decisions={
            "compute_location": "local existing hospital computer",
            "inference_strategy": "daily batch prediction",
            "storage_location": "local file system",
            "connectivity_strategy": "none (airgapped USB transfer)",
            "input_modality": "manual CSV transfer",
            "decision_mechanism": "XGBoost regression"
        }
    )
    
    scenario = BenchmarkScenario(
        name="Hospital Wait Time - Hidden DB Constraint",
        description="A hospital needs wait time predictions, but has strict constraints on cloud and internet. The hidden constraint is that direct DB access is administratively blocked.",
        problem_what="Predict patient waiting times and identify overcrowding.",
        problem_why="Hospitals need earlier intervention without expensive infrastructure.",
        problem_how="AI-based prediction using historical queue, appointment, staffing and arrival data.",
        constraints=[
            "budget <= $500/month",
            "no cloud infrastructure",
            "existing hospital computers only",
            "unreliable internet",
            "30-day prototype",
            "patient data must remain local"
        ],
        requirements=[
            Requirement(name="predict waiting time", required=True),
            Requirement(name="identify overcrowding risk", required=True),
            Requirement(name="useful accuracy", required=True),
            Requirement(name="low operating cost", required=True)
        ],
        scoring_anchors=ScoringAnchors(value_maximum=100.0, cost_budget_limit=500.0, latency_target_ms=1000.0, timeline_maximum_days=30.0),
        optimization_weights=OptimizationWeights(w_value=0.4, w_cost=0.3, w_performance=0.2, w_timeline=0.1),
        oracle_architecture=oracle_arch,
        hidden_facts_to_reveal={
            "Direct database query permissions": "NO"
        },
        evaluation_rules=get_hospital_rules(),
        expected_relevant_branches=0
    )
    write_scenario(scenario, "test_hidden_assumption.json")

if __name__ == "__main__":
    generate_test_optimal_baseline()
    generate_test_impossible()
    generate_test_irrelevant_uncertainty()
    generate_test_unselected_winner()
    generate_test_false_confidence()
    generate_test_feasible_tie()
    generate_test_hidden_assumption()
