from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import hashlib
from decision_engine.tree.optimizer import OptimizationResult, PathNode, compute_graph_fingerprint
from decision_engine.tree.context import DecisionContext, canonicalize_json

class RecommendationResponse(BaseModel):
    action: str
    recommended_path_id: Optional[str] = None
    epistemic_warnings: Optional[Dict[str, Any]] = None
    
    severity: str = "INFO"
    violations: List[str] = []
    graph_state: str = "VALID"
    context_state: str = "VALID"
    epistemic_state: str = "VALID"
    policy_state: str = "VALID"
    integrity_state: str = "VALID"

def generate_recommendation(
    serialized_optimization_result: str, 
    current_context: DecisionContext,
    current_graph: List[PathNode],
    current_graph_version: str = "v1"
) -> RecommendationResponse:
    try:
        opt = OptimizationResult.model_validate_json(serialized_optimization_result)
    except Exception as e:
        return RecommendationResponse(
            action="REJECT",
            severity="FATAL",
            violations=["COMPROMISED_DECISION_INTEGRITY"],
            integrity_state="COMPROMISED",
            epistemic_warnings={"reason": "COMPROMISED_DECISION_INTEGRITY"}
        )
        
    violations = []
    integrity_state = "VALID"
    graph_state = "VALID"
    context_state = "VALID"
    epistemic_state = "VALID"
    
    decision_data = {
        "best_path_id": opt.best_path_id,
        "status": opt.status,
        "effective_score": opt.effective_score,
        "context_fingerprint": opt.context_fingerprint,
        "graph_fingerprint": opt.graph_fingerprint,
        "graph_version": opt.graph_version,
        "best_architecture": opt.best_architecture.model_dump() if opt.best_architecture else None
    }
    expected_decision_fingerprint = hashlib.sha256(canonicalize_json(decision_data).encode('utf-8')).hexdigest()
    if opt.decision_fingerprint != expected_decision_fingerprint:
        violations.append("COMPROMISED_DECISION_INTEGRITY")
        integrity_state = "COMPROMISED"
        
    if opt.graph_version != current_graph_version:
        if "INVALIDATED_DECISION_ARTIFACT" not in violations:
            violations.append("INVALIDATED_DECISION_ARTIFACT")
        integrity_state = "COMPROMISED"
        
    live_graph_fingerprint = compute_graph_fingerprint(current_graph)
    if opt.graph_fingerprint != live_graph_fingerprint:
        graph_state = "DRIFTED"
        live_winner = next((n for n in current_graph if n.id == opt.best_path_id), None)
        if live_winner is None or live_winner.architecture.get_fingerprint() != opt.best_architecture.get_fingerprint():
            if "INVALIDATED_DECISION_ARTIFACT" not in violations:
                violations.append("INVALIDATED_DECISION_ARTIFACT")
            integrity_state = "COMPROMISED"
        else:
            if "STALE_DECISION_GRAPH" not in violations:
                violations.append("STALE_DECISION_GRAPH")

    if opt.context_fingerprint != current_context.get_fingerprint():
        violations.append("STALE_DECISION_CONTEXT")
        context_state = "DRIFTED"
        
    if opt.status == "UNRESOLVED":
        violations.append("UNRESOLVED_DEPENDENCY")
        epistemic_state = "UNRESOLVED"
        
    if "COMPROMISED_DECISION_INTEGRITY" in violations or "INVALIDATED_DECISION_ARTIFACT" in violations:
        action = "REJECT"
        severity = "FATAL"
    elif len(violations) > 0:
        action = "HOLD_FOR_REVIEW"
        severity = "WARNING"
    else:
        if opt.status == "TERMINAL":
            action = "RECOMMEND"
        elif opt.status == "REJECTED" or opt.status.startswith("NO_"):
            action = "REJECT"
        else:
            action = "HOLD_FOR_REVIEW"
        severity = "INFO"
        
    VIOLATION_ORDER = {
        "COMPROMISED_DECISION_INTEGRITY": 10,
        "INVALIDATED_DECISION_ARTIFACT": 20,
        "STALE_DECISION_GRAPH": 30,
        "STALE_DECISION_CONTEXT": 40,
        "POLICY_STATE_CHANGED": 50,
        "UNRESOLVED_DEPENDENCY": 60,
        "ROBUSTNESS_DRIFT": 70
    }
    violations.sort(key=lambda x: VIOLATION_ORDER.get(x, 100))
    
    warnings = {"reason": violations[0]} if violations else None
    
    return RecommendationResponse(
        action=action,
        recommended_path_id=opt.best_path_id,
        epistemic_warnings=warnings,
        severity=severity,
        violations=violations,
        graph_state=graph_state,
        context_state=context_state,
        epistemic_state=epistemic_state,
        policy_state="VALID",
        integrity_state=integrity_state
    )
