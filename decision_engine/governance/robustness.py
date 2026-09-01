from pydantic import BaseModel
from typing import List, Dict
from decision_engine.input_layer.ontology import evaluate_ontology

class FutureScenario(BaseModel):
    id: str
    environment_constraints: List[str]
    family_id: str = "default"
    probability: float = 1.0
    impact: float = 1.0

class RobustnessProfile(BaseModel):
    survival_rate: float
    family_worst_case_survival: float
    expected_robustness_loss: float
    failed_scenarios: List[str]
    fragility_reasons: Dict[str, List[str]]

def evaluate_robustness(candidate, scenarios: List[FutureScenario], known_dependencies: List[str]) -> RobustnessProfile:
    from decision_engine.tree.optimizer import evaluate_node_state

    if not scenarios:
        return RobustnessProfile(
            survival_rate=1.0, 
            family_worst_case_survival=1.0, 
            expected_robustness_loss=0.0, 
            failed_scenarios=[], 
            fragility_reasons={}
        )
        
    sorted_scenarios = sorted(scenarios, key=lambda s: s.id)
    
    unique_scenarios = {}
    for sc in sorted_scenarios:
        key = frozenset(sc.environment_constraints)
        if key not in unique_scenarios:
            unique_scenarios[key] = {
                "scenario": sc,
                "probability_mass": sc.probability,
                "max_impact": sc.impact,
                "family_id": sc.family_id
            }
        else:
            unique_scenarios[key]["probability_mass"] += sc.probability
            unique_scenarios[key]["max_impact"] = max(unique_scenarios[key]["max_impact"], sc.impact)

    total_prob = sum(item["probability_mass"] for item in unique_scenarios.values())
    if total_prob > 0:
        for item in unique_scenarios.values():
            item["probability_mass"] /= total_prob
            
    total_raw = len(sorted_scenarios)
    failed_raw = 0
    failed_raw_ids = []
    reasons = {}

    for sc in sorted_scenarios:
        res = evaluate_ontology(candidate.architecture, sc.environment_constraints, [])
        passes_hard_gates = len(res.constraint_failures) == 0 and len(res.requirement_failures) == 0
        unknowns = [d for d in candidate.architecture.semantic_dependencies if d not in known_dependencies]
        status = evaluate_node_state(
            node=None, is_leaf=True, has_unknowns=len(unknowns) > 0, passes_hard_gates=passes_hard_gates
        )
        if status == "REJECTED":
            failed_raw += 1
            failed_raw_ids.append(sc.id)
            reasons[sc.id] = res.constraint_failures + res.requirement_failures
            
    raw_survival_rate = (total_raw - failed_raw) / total_raw if total_raw > 0 else 1.0

    failed_unique_keys = set()
    failed_families = set()
    all_families = set(item["family_id"] for item in unique_scenarios.values())
    expected_loss = 0.0

    for key, item in unique_scenarios.items():
        sc = item["scenario"]
        res = evaluate_ontology(candidate.architecture, sc.environment_constraints, [])
        passes_hard_gates = len(res.constraint_failures) == 0 and len(res.requirement_failures) == 0
        unknowns = [d for d in candidate.architecture.semantic_dependencies if d not in known_dependencies]
        status = evaluate_node_state(
            node=None, is_leaf=True, has_unknowns=len(unknowns) > 0, passes_hard_gates=passes_hard_gates
        )
        
        if status == "REJECTED":
            failed_unique_keys.add(key)
            failed_families.add(item["family_id"])
            expected_loss += (item["probability_mass"] * item["max_impact"])

    family_worst_case_survival = 1.0
    if len(all_families) > 0:
        completely_survived_families = len(all_families) - len(failed_families)
        family_worst_case_survival = completely_survived_families / len(all_families)
        
    return RobustnessProfile(
        survival_rate=raw_survival_rate,
        family_worst_case_survival=family_worst_case_survival,
        expected_robustness_loss=expected_loss,
        failed_scenarios=failed_raw_ids,
        fragility_reasons=reasons
    )
