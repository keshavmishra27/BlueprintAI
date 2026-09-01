from typing import List
from pydantic import BaseModel
from decision_engine.input_layer.schemas import ArchitectureNode

INFEASIBLE_SENTINEL = -1000.0

class ScoringAnchors(BaseModel):
    value_maximum: float
    cost_budget_limit: float
    latency_target_ms: float
    timeline_maximum_days: float

class OptimizationWeights(BaseModel):
    w_value: float
    w_cost: float
    w_performance: float
    w_timeline: float

class EvaluationRule(BaseModel):
    target_field: str
    match_string: str
    metric: str
    operation: str
    value: float

class DeterministicEvaluationRules(BaseModel):
    base_cost: float = 100.0
    base_latency_ms: float = 1000.0
    base_timeline_days: float = 10.0
    base_value: float = 80.0
    rules: List[EvaluationRule] = []

def compute_s_abs(
    is_feasible: bool,
    estimated_value: float,
    estimated_cost: float,
    estimated_latency_ms: float,
    estimated_timeline_days: float,
    anchors: ScoringAnchors,
    weights: OptimizationWeights
) -> float:
    """
    Computes the absolute score S_abs for a candidate architecture using the Global Anchor Scoring System (GASS).
    """
    if not is_feasible:
        return globals().get('INFEASIBLE_SENTINEL', -1000.0)
        
    v_n = min(1.0, estimated_value / anchors.value_maximum)
    c_n = min(1.0, estimated_cost / anchors.cost_budget_limit)
    p_n = min(1.0, anchors.latency_target_ms / estimated_latency_ms) if estimated_latency_ms > 0 else 1.0
    t_n = min(1.0, anchors.timeline_maximum_days / estimated_timeline_days) if estimated_timeline_days > 0 else 1.0
    
    return (weights.w_value * v_n) + (weights.w_performance * p_n) + (weights.w_timeline * t_n) - (weights.w_cost * c_n)

def get_field_value(arch_dict: dict, field_path: str) -> str:
    """Helper to extract a nested field value as a string."""
    parts = field_path.split(".")
    current = arch_dict
    for p in parts:
        if isinstance(current, dict) and p in current:
            current = current[p]
        else:
            return ""
    if isinstance(current, list):
        return " ".join(str(x) for x in current).lower()
    return str(current).lower()

def evaluate_architecture_metrics(arch: ArchitectureNode, rules: DeterministicEvaluationRules) -> dict:
    """
    Scenario-driven deterministic evaluator.
    Applies rules against structured fields to modify base metrics.
    """
    cost = rules.base_cost
    latency_ms = rules.base_latency_ms
    timeline_days = rules.base_timeline_days
    value = rules.base_value
    
    arch_dict = arch.model_dump()
    
    for rule in rules.rules:
        field_val = get_field_value(arch_dict, rule.target_field)
        if rule.match_string.lower() in field_val:
            if rule.metric == "cost":
                if rule.operation == "add": cost += rule.value
                elif rule.operation == "set": cost = rule.value
                elif rule.operation == "multiply": cost *= rule.value
            elif rule.metric == "latency_ms":
                if rule.operation == "add": latency_ms += rule.value
                elif rule.operation == "set": latency_ms = rule.value
                elif rule.operation == "multiply": latency_ms *= rule.value
            elif rule.metric == "timeline_days":
                if rule.operation == "add": timeline_days += rule.value
                elif rule.operation == "set": timeline_days = rule.value
                elif rule.operation == "multiply": timeline_days *= rule.value
            elif rule.metric == "value":
                if rule.operation == "add": value += rule.value
                elif rule.operation == "set": value = rule.value
                elif rule.operation == "multiply": value *= rule.value
                
    return {
        "estimated_value": value,
        "estimated_cost": cost,
        "estimated_latency_ms": latency_ms,
        "estimated_timeline_days": timeline_days
    }
