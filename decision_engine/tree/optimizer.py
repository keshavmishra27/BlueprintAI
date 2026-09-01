from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from decision_engine.tree.tree_schemas import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode

class OptimizationResult(BaseModel):
    status: str
    best_path_id: Optional[str] = None
    best_architecture: Optional[ArchitectureNode] = None
    candidates_evaluated: int = 0
    effective_score: Optional[float] = None
    epistemic_risk: Optional[float] = None
    survival_rate: Optional[float] = None
    family_worst_case_survival: Optional[float] = None
    expected_robustness_loss: Optional[float] = None
    pareto_frontier: List[str] = []
    graph_version: str = "v1"
    graph_fingerprint: Optional[str] = None
    context_fingerprint: Optional[str] = None
    decision_fingerprint: Optional[str] = None

from decision_engine.input_layer.ontology import get_known_dependencies
from decision_engine.tree.context import DecisionContext, canonicalize_json
from decision_engine.governance.robustness import evaluate_robustness, FutureScenario
import hashlib

def evaluate_node_state(node: PathNode, is_leaf: bool, has_unknowns: bool, passes_hard_gates: bool) -> str:
    """
    Determines the state of a node in the decision tree based on evaluation rules.
    """
    if not passes_hard_gates:
        return "REJECTED"
    if has_unknowns:
        return "UNRESOLVED"
    if is_leaf:
        return "TERMINAL"
    return "ACTIVE"

def compute_graph_fingerprint(decision_graph: List[PathNode]) -> str:
    graph_representation = []
    for node in sorted(decision_graph, key=lambda x: x.id):
        deps = sorted(node.architecture.semantic_dependencies) if node.architecture else []
        node_rep = {
            "id": node.id,
            "parent_id": node.parent_id,
            "status": node.status,
            "path_score": node.path_score,
            "path_cost": node.path_cost,
            "operational_complexity": node.operational_complexity,
            "semantic_dependencies": deps,
            "architecture_fingerprint": node.architecture.get_fingerprint() if node.architecture else None
        }
        graph_representation.append(node_rep)
    
    canonical_json = canonicalize_json(graph_representation)
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

def optimize_tree(decision_graph: List[PathNode], context: DecisionContext, graph_version: str = "v1") -> OptimizationResult:
    """
    Finds the optimal terminal or unresolved candidate in the decision graph.
    Applies epistemic risk penalties.
    """
    terminal_candidates = [n for n in decision_graph if n.status in ["TERMINAL", "UNRESOLVED"]]
    needs_info = [n for n in decision_graph if n.status == "NEEDS_INFORMATION"]
    unexplored = [n for n in decision_graph if n.status == "UNEXPLORED_HYPOTHESIS"]
    
    if needs_info or unexplored:
        return OptimizationResult(status="CONTINUE", candidates_evaluated=len(terminal_candidates))
        
    if not terminal_candidates:
        return OptimizationResult(status="NO_FEASIBLE_ARCHITECTURE_FOUND")
        
    epistemic_lambda = context.optimizer_preferences.get("epistemic_lambda", 0.0)
    robustness_lambda = context.optimizer_preferences.get("robustness_lambda", 0.0)
    cost_lambda = context.optimizer_preferences.get("cost_lambda", 0.0)
    complexity_lambda = context.optimizer_preferences.get("complexity_lambda", 0.0)
    
    future_scenarios = []
    if context.future_scenarios:
        future_scenarios = [FutureScenario(**s) for s in context.future_scenarios]
        
    known_deps = get_known_dependencies()
        
    best_candidate = None
    best_effective_score = None
    best_epistemic_risk = None
    best_survival_rate = None
    best_family_survival = None
    best_expected_loss = None
    best_raw_score = -float('inf')
    best_fingerprint = ""
    
    metrics_map = {}
    for candidate in terminal_candidates:
        candidate_deps = candidate.architecture.semantic_dependencies
        unknowns = [d for d in candidate_deps if d not in known_deps]
        epistemic_risk = float(len(unknowns))
        
        survival_rate = 1.0
        family_survival = 1.0
        expected_loss = 0.0
        if future_scenarios:
            profile = evaluate_robustness(candidate, future_scenarios, known_deps)
            survival_rate = profile.survival_rate
            family_survival = profile.family_worst_case_survival
            expected_loss = profile.expected_robustness_loss
            
        metrics_map[candidate.id] = {
            "perf": candidate.path_score or 0.0,
            "cost": candidate.path_cost or 0.0,
            "comp": candidate.operational_complexity or 0.0,
            "epis": epistemic_risk,
            "rob_raw": survival_rate,
            "rob_fam": family_survival,
            "rob_loss": expected_loss
        }

    pareto_frontier = []
    for cand_id, m1 in metrics_map.items():
        dominated = False
        for other_id, m2 in metrics_map.items():
            if cand_id == other_id:
                continue
            better_or_eq_on_all = (
                m2["perf"] >= m1["perf"] and
                m2["cost"] <= m1["cost"] and
                m2["comp"] <= m1["comp"] and
                m2["rob_raw"] >= m1["rob_raw"]
            )
            strictly_better_on_one = (
                m2["perf"] > m1["perf"] or
                m2["cost"] < m1["cost"] or
                m2["comp"] < m1["comp"] or
                m2["rob_raw"] > m1["rob_raw"]
            )
            if better_or_eq_on_all and strictly_better_on_one:
                dominated = True
                break
        if not dominated:
            pareto_frontier.append(cand_id)
            
    for candidate in terminal_candidates:
        m = metrics_map[candidate.id]
        
        eff_score = m["perf"] - (epistemic_lambda * m["epis"])
        eff_score -= cost_lambda * m["cost"]
        eff_score -= complexity_lambda * m["comp"]
        
        strategy = context.optimizer_preferences.get("robustness_strategy", "raw")
        if strategy == "raw":
            eff_score += robustness_lambda * m["rob_raw"]
        elif strategy == "family_worst_case":
            eff_score += robustness_lambda * m["rob_fam"]
        elif strategy == "weighted":
            eff_score -= robustness_lambda * m["rob_loss"]
            
        if best_effective_score is None:
            best_candidate = candidate
            best_effective_score = eff_score
            best_epistemic_risk = m["epis"]
            best_survival_rate = m["rob_raw"]
            best_family_survival = m["rob_fam"]
            best_expected_loss = m["rob_loss"]
        else:
            if eff_score > best_effective_score:
                best_candidate = candidate
                best_effective_score = eff_score
                best_epistemic_risk = m["epis"]
                best_survival_rate = m["rob_raw"]
                best_family_survival = m["rob_fam"]
                best_expected_loss = m["rob_loss"]
            elif abs(eff_score - best_effective_score) < 1e-6:
                if m["epis"] < best_epistemic_risk:
                    best_candidate = candidate
                    best_effective_score = eff_score
                    best_epistemic_risk = m["epis"]
                    best_survival_rate = m["rob_raw"]
                    best_family_survival = m["rob_fam"]
                    best_expected_loss = m["rob_loss"]
                elif abs(m["epis"] - best_epistemic_risk) < 1e-6:
                    if m["rob_raw"] > best_survival_rate:
                        best_candidate = candidate
                        best_effective_score = eff_score
                        best_epistemic_risk = m["epis"]
                        best_survival_rate = m["rob_raw"]
                        best_family_survival = m["rob_fam"]
                        best_expected_loss = m["rob_loss"]
                    elif abs(m["rob_raw"] - best_survival_rate) < 1e-6:
                        if candidate.id > best_candidate.id:
                            best_candidate = candidate
                            best_effective_score = eff_score
                            best_epistemic_risk = m["epis"]
                            best_survival_rate = m["rob_raw"]
                            best_family_survival = m["rob_fam"]
                            best_expected_loss = m["rob_loss"]
            
    if best_candidate:
        res = OptimizationResult(
            status=best_candidate.status, 
            best_path_id=best_candidate.id, 
            best_architecture=best_candidate.architecture,
            candidates_evaluated=len(terminal_candidates),
            effective_score=best_effective_score,
            epistemic_risk=best_epistemic_risk,
            survival_rate=best_survival_rate,
            family_worst_case_survival=best_family_survival,
            expected_robustness_loss=best_expected_loss,
            pareto_frontier=sorted(pareto_frontier),
            graph_version=graph_version
        )
        
        res.context_fingerprint = context.get_fingerprint()
        res.graph_fingerprint = compute_graph_fingerprint(decision_graph)
        
        decision_data = {
            "best_path_id": res.best_path_id,
            "status": res.status,
            "effective_score": res.effective_score,
            "context_fingerprint": res.context_fingerprint,
            "graph_fingerprint": res.graph_fingerprint,
            "graph_version": res.graph_version,
            "best_architecture": res.best_architecture.model_dump() if res.best_architecture else None
        }
        res.decision_fingerprint = hashlib.sha256(canonicalize_json(decision_data).encode('utf-8')).hexdigest()
        return res
        
    return OptimizationResult(status="NO_FEASIBLE_ARCHITECTURE_FOUND")
