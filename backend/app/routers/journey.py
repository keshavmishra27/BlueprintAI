import uuid
import copy
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from decision_engine.tree.tree_schemas import (
    ProjectState,
    ArchitectureNode,
    AgentUncertainty,
    TreeState,
    ArchitectureState,
    PathNode
)
from decision_engine.input_layer.evaluator import evaluate_battle
from decision_engine.tree.optimizer import optimize_tree, evaluate_node_state
from decision_engine.tree.question_generator import evaluate_provided_uncertainties, select_best_question
from decision_engine.input_layer.epistemic_validator import validate_epistemic_boundaries, EpistemicStatus
from idea_refiner.schema import RequirementArtifact, ConnectivityType
from decision_engine.tree.loop_detector import detect_loop, compute_epistemic_state_hash

def has_resolving_uncertainty(unproven_gaps: List[str], candidate_uncertainties: List[AgentUncertainty]) -> bool:
    gap_to_target_map = {
        "requires_continuous_connectivity": "network.connectivity",
        "requires_realtime_operational_data": "data_freshness.real_time_streams_required"
    }
    
    needed_targets = {gap_to_target_map.get(gap) for gap in unproven_gaps if gap_to_target_map.get(gap)}
    
    for unc in candidate_uncertainties:
        if unc.question_target in needed_targets:
            return True
            
    return False
from benchmark_suite.schemas import BenchmarkScenario
from decision_engine.tree.benchmark_evaluator import (
    evaluate_architecture_metrics,
    compute_s_abs,
    DeterministicEvaluationRules,
    OptimizationWeights,
    ScoringAnchors
)

router = APIRouter(prefix="/api/journey", tags=["journey"])

sessions: Dict[str, TreeState] = {}
private_sessions: Dict[str, BenchmarkScenario] = {}

class JourneyStateResponse(BaseModel):
    session_id: str
    decision_graph: List[PathNode]
    project_state: ProjectState
    battle_history: List[Any]

class JourneyStartRequest(BaseModel):
    session_id: str
    project_state: ProjectState
    initial_architecture: ArchitectureNode
    candidate_uncertainties: List[AgentUncertainty]
    private_context: Optional[BenchmarkScenario] = None
    epistemic_requirements: Optional[RequirementArtifact] = None

class JourneyResponse(BaseModel):
    status: str
    selected_uncertainty_id: Optional[str] = None
    selected_uncertainty_text: Optional[str] = None
    selection_reason: Optional[Dict[str, Any]] = None
    best_path_id: Optional[str] = None
    best_score: Optional[float] = None
    exploration_trace: Optional[List[Dict[str, Any]]] = None

class JourneyAnswerRequest(BaseModel):
    session_id: str
    parent_node_id: str
    answer: str
    generated_architecture: ArchitectureNode
    candidate_uncertainties: List[AgentUncertainty]
    is_user_selected: bool = False
    epistemic_resolutions: Dict[str, str] = {}

class EvaluateRequest(BaseModel):
    project_state: ProjectState
    architecture: ArchitectureNode
    private_context: Optional[BenchmarkScenario] = None

class EvaluateResponse(BaseModel):
    feasible: bool
    requirements_met: int
    metrics: Dict[str, Any]

@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_architecture(req: EvaluateRequest):
    battle_result = evaluate_battle(
        req.architecture,
        req.architecture,
        req.project_state.current_constraints,
        req.project_state.current_requirements
    )
    
    rules = req.private_context.evaluation_rules if req.private_context else DeterministicEvaluationRules()
    metrics = evaluate_architecture_metrics(req.architecture, rules)
    
    reqs_met = sum(1 for r in battle_result.requirement_evaluations if r.player_b_satisfies)
    
    return EvaluateResponse(
        feasible=battle_result.b_feasible,
        requirements_met=reqs_met,
        metrics=metrics
    )

@router.post("/start", response_model=JourneyResponse)
def start_journey(req: JourneyStartRequest):
    if req.private_context:
        private_sessions[req.session_id] = req.private_context
        
    p_state = req.project_state
    
    user_arch_state = ArchitectureState(
        architecture=req.initial_architecture,
        generation=1,
        based_on="User original input"
    )
    
    b_arch_state = ArchitectureState(
        architecture=req.initial_architecture,
        generation=1,
        based_on="Gemini initial proposal"
    )
    
    epistemic_status = EpistemicStatus.NOT_APPLICABLE
    unproven_gaps = []
    
    if req.epistemic_requirements:
        epistemic_status, unproven_gaps = validate_epistemic_boundaries(b_arch_state.architecture, req.epistemic_requirements)
        
    battle_result = None
    if epistemic_status == EpistemicStatus.CONTRADICTED:
        root_status = "REJECTED"
    elif epistemic_status == EpistemicStatus.UNPROVEN:
        if has_resolving_uncertainty(unproven_gaps, req.candidate_uncertainties):
            root_status = "NEEDS_INFORMATION"
        else:
            root_status = "INVALID_CANDIDATE"
    elif epistemic_status == EpistemicStatus.INVALID_CANDIDATE:
        root_status = "INVALID_CANDIDATE"
    else:
        battle_result = evaluate_battle(
            user_arch_state.architecture, 
            b_arch_state.architecture, 
            p_state.current_constraints, 
            p_state.current_requirements
        )
    
    tree_state = TreeState(
        current_state_id="level_0",
        project_state=p_state,
        user_architecture=user_arch_state,
        player_b_architecture=b_arch_state,
        battle_history=[battle_result] if battle_result else [],
        decision_graph=[],
        epistemic_requirements=req.epistemic_requirements
    )
    sessions[req.session_id] = tree_state
    
    evaluated_uncs = evaluate_provided_uncertainties(
        req.candidate_uncertainties,
        b_arch_state,
        user_arch_state,
        p_state
    )
    
    agent_uncs_map = {u.id: u for u in req.candidate_uncertainties}
    best_q = select_best_question(evaluated_uncs, agent_uncs_map)
    
    root_node_id = str(uuid.uuid4())
    
    if epistemic_status in (EpistemicStatus.SATISFIED, EpistemicStatus.NOT_APPLICABLE):
        root_status = evaluate_node_state(
            None, 
            is_leaf=True, 
            has_unknowns=bool(best_q), 
            passes_hard_gates=battle_result.b_feasible
        )
    
    priv = private_sessions.get(req.session_id)
    rules = priv.evaluation_rules if priv else DeterministicEvaluationRules()
    weights = priv.optimization_weights if priv else OptimizationWeights(w_value=0.5, w_cost=0.5, w_performance=0.0, w_timeline=0.0)
    anchors = priv.scoring_anchors if priv else ScoringAnchors(value_maximum=100.0, cost_budget_limit=1000.0, latency_target_ms=100.0, timeline_maximum_days=10.0)
    
    root_metrics = evaluate_architecture_metrics(b_arch_state.architecture, rules)
    s_abs = None
    if battle_result:
        s_abs = compute_s_abs(
            battle_result.b_feasible, 
            root_metrics["estimated_value"], 
            root_metrics["estimated_cost"], 
            root_metrics["estimated_latency_ms"], 
            root_metrics["estimated_timeline_days"], 
            anchors, 
            weights
        )
    
    loop_hash = None
    if best_q:
        loop_hash = compute_epistemic_state_hash(
            best_q.uncertainty.question_target,
            req.epistemic_requirements,
            {},
            b_arch_state.architecture.semantic_dependencies
        )
        
    root_node = PathNode(
        id=root_node_id,
        parent_id=None,
        architecture=b_arch_state.architecture,
        status=root_status,
        path_cost=root_metrics["estimated_cost"],
        path_value=root_metrics["estimated_value"],
        path_latency=root_metrics["estimated_latency_ms"],
        path_timeline=root_metrics["estimated_timeline_days"],
        path_score=s_abs,
        reject_reasons=battle_result.b_constraint_violations if battle_result else [],
        selected_by_user=True,
        epistemic_status=epistemic_status.value if epistemic_status else None,
        epistemic_evidence={},
        loop_identity_hash=loop_hash
    )
    tree_state.decision_graph.append(root_node)
    
    if best_q:
        for option_key, option in best_q.options.items():
            hypo_node = PathNode(
                id=str(uuid.uuid4()),
                parent_id=root_node_id,
                architecture=option.candidate_architecture,
                status="UNEXPLORED_HYPOTHESIS",
                path_cost=None,
                path_value=None,
                selected_by_user=False,
                question_that_produced_it=best_q.question_text,
                uncertainty_target=best_q.uncertainty.question_target,
                user_answer=option_key
            )
            tree_state.decision_graph.append(hypo_node)
    
    trace = []
    for unc in evaluated_uncs:
        agent_unc = agent_uncs_map[unc.id]
        is_selected = (best_q is not None and best_q.uncertainty.id == unc.id)
        
        branch_generated = agent_unc.yes_candidate_architecture is not None and agent_unc.no_candidate_architecture is not None
        branch_feasible = (unc.yes_outcome.b_feasible if unc.yes_outcome else False) or (unc.no_outcome.b_feasible if unc.no_outcome else False)
        
        trace.append({
            "question_id": unc.id,
            "question_text": agent_unc.question_text,
            "impact_score": unc.decision_impact_score,
            "selected": is_selected,
            "user_answer": "N/A",
            "branch_generated": branch_generated,
            "branch_valid": True,
            "branch_feasible": branch_feasible,
            "branch_score": 0.0
        })

    if best_q:
        return JourneyResponse(
            status="CONTINUE",
            selected_uncertainty_id=best_q.uncertainty.id,
            selected_uncertainty_text=best_q.question_text,
            selection_reason={
                "method": "impact_score",
                "score": best_q.uncertainty.decision_impact_score
            },
            exploration_trace=trace
        )
    else:
        from decision_engine.tree.context import DecisionContext
        empty_context = DecisionContext(
            ontology_version="v1",
            registry_policy_hashes=[],
            environment_constraints=[],
            optimizer_preferences={}
        )
        res = optimize_tree(tree_state.decision_graph, empty_context)
        return JourneyResponse(
            status=res.status,
            best_path_id=res.best_path_id,
            best_score=0.0,
            exploration_trace=trace
        )

@router.get("/{session_id}/state", response_model=JourneyStateResponse)
def get_journey_state(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    tree = sessions[session_id]
    return JourneyStateResponse(
        session_id=session_id,
        decision_graph=tree.decision_graph,
        project_state=tree.project_state,
        battle_history=tree.battle_history
    )

@router.post("/answer", response_model=JourneyResponse)
def answer_journey(req: JourneyAnswerRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    tree_state = sessions[req.session_id]
    
    parent_node = next((n for n in tree_state.decision_graph if n.id == req.parent_node_id), None)
        
    b_arch_state = ArchitectureState(
        architecture=req.generated_architecture,
        generation=tree_state.player_b_architecture.generation + 1,
        based_on=f"Answer {req.answer} to uncertainty"
    )
    tree_state.player_b_architecture = b_arch_state
    
    uncertainty_node = next((n for n in tree_state.decision_graph 
                             if n.parent_id == req.parent_node_id and n.user_answer == req.answer and n.status == "UNEXPLORED_HYPOTHESIS"), None)
    
    if not uncertainty_node:
        raise HTTPException(status_code=400, detail="Unexplored hypothesis not found")
        
    epistemic_evidence = dict(parent_node.epistemic_evidence) if parent_node and parent_node.epistemic_evidence else {}
    
    target_unc_target = uncertainty_node.uncertainty_target if uncertainty_node else None
    
    if target_unc_target and req.epistemic_resolutions:
        if target_unc_target in req.epistemic_resolutions:
            val = req.epistemic_resolutions[target_unc_target]
            
            if target_unc_target == "network.connectivity":
                if val not in [e.value for e in ConnectivityType]:
                    raise HTTPException(status_code=400, detail=f"Invalid value {val} for target {target_unc_target}")
                epistemic_evidence[target_unc_target] = val
            elif target_unc_target == "data_freshness.real_time_streams_required":
                if str(val).lower() not in ["true", "false"]:
                    raise HTTPException(status_code=400, detail=f"Invalid value {val} for target {target_unc_target}")
                epistemic_evidence[target_unc_target] = val
            else:
                raise HTTPException(status_code=400, detail=f"Unknown ontology target: {target_unc_target}")

    epistemic_status = EpistemicStatus.NOT_APPLICABLE
    unproven_gaps = []
    
    if tree_state.epistemic_requirements:
        epistemic_status, unproven_gaps = validate_epistemic_boundaries(b_arch_state.architecture, tree_state.epistemic_requirements, branch_evidence=epistemic_evidence)
        
    battle_result = None
    if epistemic_status == EpistemicStatus.CONTRADICTED:
        node_status = "REJECTED"
        best_q = None
        evaluated_uncs = []
    elif epistemic_status == EpistemicStatus.INVALID_CANDIDATE:
        node_status = "INVALID_CANDIDATE"
        best_q = None
        evaluated_uncs = []
    elif epistemic_status == EpistemicStatus.UNPROVEN:
        node_status = "UNPROVEN"
        battle_result = None
        best_q = None
        remaining_uncs = req.candidate_uncertainties
        
        evaluated_uncs = evaluate_provided_uncertainties(
            remaining_uncs,
            b_arch_state,
            tree_state.user_architecture,
            tree_state.project_state
        )
        agent_uncs_map = {u.id: u for u in remaining_uncs}
        best_q = select_best_question(evaluated_uncs, agent_uncs_map)
    else:
        battle_result = evaluate_battle(
            tree_state.user_architecture.architecture, 
            b_arch_state.architecture, 
            tree_state.project_state.current_constraints, 
            tree_state.project_state.current_requirements
        )
        tree_state.battle_history.append(battle_result)
        
        remaining_uncs = [u for u in req.candidate_uncertainties if u.question_target != target_unc_target] if target_unc_target else req.candidate_uncertainties
        
        evaluated_uncs = evaluate_provided_uncertainties(
            remaining_uncs,
            b_arch_state,
            tree_state.user_architecture,
            tree_state.project_state
        )
        agent_uncs_map = {u.id: u for u in remaining_uncs}
        best_q = select_best_question(evaluated_uncs, agent_uncs_map)
    if best_q:
        loop_detected = detect_loop(
            current_target=best_q.uncertainty.question_target,
            current_requirements=tree_state.epistemic_requirements,
            current_evidence=epistemic_evidence,
            current_dependencies=b_arch_state.architecture.semantic_dependencies,
            decision_graph=tree_state.decision_graph,
            parent_node_id=req.parent_node_id
        )
        if loop_detected:
            raise HTTPException(status_code=400, detail="Infinite loop detected: Repeated semantic question")
            
    MAX_TURNS = 5
    if b_arch_state.generation >= MAX_TURNS:
        best_q = None
        if epistemic_status == EpistemicStatus.UNPROVEN:
            node_status = "MAX_TURNS_REACHED"
        elif epistemic_status == EpistemicStatus.INVALID_CANDIDATE:
            node_status = "INVALID_CANDIDATE"
            
    if epistemic_status == EpistemicStatus.UNPROVEN and node_status != "MAX_TURNS_REACHED":
        if best_q:
            node_status = "NEEDS_INFORMATION"
        else:
            node_status = "INVALID_CANDIDATE"
    
    new_node_id = str(uuid.uuid4())
    
    if epistemic_status in (EpistemicStatus.SATISFIED, EpistemicStatus.NOT_APPLICABLE):
        node_status = evaluate_node_state(
            None, 
            is_leaf=True, 
            has_unknowns=bool(best_q), 
            passes_hard_gates=battle_result.b_feasible
        )
    
    if parent_node:
        parent_node.status = "ACTIVE"
        
    priv = private_sessions.get(req.session_id)
    rules = priv.evaluation_rules if priv else DeterministicEvaluationRules()
    weights = priv.optimization_weights if priv else OptimizationWeights(w_value=0.5, w_cost=0.5, w_performance=0.0, w_timeline=0.0)
    anchors = priv.scoring_anchors if priv else ScoringAnchors(value_maximum=100.0, cost_budget_limit=1000.0, latency_target_ms=100.0, timeline_maximum_days=10.0)
    
    new_metrics = evaluate_architecture_metrics(b_arch_state.architecture, rules)
    s_abs = None
    if battle_result:
        s_abs = compute_s_abs(
            battle_result.b_feasible, 
            new_metrics["estimated_value"], 
            new_metrics["estimated_cost"], 
            new_metrics["estimated_latency_ms"], 
            new_metrics["estimated_timeline_days"], 
            anchors, 
            weights
        )
        
    new_loop_hash = None
    if best_q:
        new_loop_hash = compute_epistemic_state_hash(
            best_q.uncertainty.question_target,
            tree_state.epistemic_requirements,
            epistemic_evidence,
            b_arch_state.architecture.semantic_dependencies
        )
        
    new_node = PathNode(
        id=new_node_id,
        parent_id=req.parent_node_id,
        architecture=b_arch_state.architecture,
        status=node_status,
        path_cost=new_metrics["estimated_cost"],
        path_value=new_metrics["estimated_value"],
        path_latency=new_metrics["estimated_latency_ms"],
        path_timeline=new_metrics["estimated_timeline_days"],
        path_score=s_abs,
        reject_reasons=battle_result.b_constraint_violations if battle_result else [],
        selected_by_user=req.is_user_selected,
        user_answer=req.answer,
        epistemic_status=epistemic_status.value if epistemic_status else None,
        epistemic_evidence=epistemic_evidence,
        question_that_produced_it=uncertainty_node.question_that_produced_it if uncertainty_node else None,
        loop_identity_hash=new_loop_hash
    )
    
    hypothesis_node_idx = next((i for i, n in enumerate(tree_state.decision_graph) 
                                if n.parent_id == req.parent_node_id and n.user_answer == req.answer and n.status == "UNEXPLORED_HYPOTHESIS"), None)
    if hypothesis_node_idx is not None:
        tree_state.decision_graph[hypothesis_node_idx] = new_node
    else:
        tree_state.decision_graph.append(new_node)
        
    if best_q:
        for option_key, option in best_q.options.items():
            hypo_node = PathNode(
                id=str(uuid.uuid4()),
                parent_id=new_node_id,
                architecture=option.candidate_architecture,
                status="UNEXPLORED_HYPOTHESIS",
                path_cost=None,
                path_value=None,
                selected_by_user=False,
                question_that_produced_it=best_q.question_text,
                uncertainty_target=best_q.uncertainty.question_target,
                user_answer=option_key
            )
            tree_state.decision_graph.append(hypo_node)
    
    from decision_engine.tree.context import DecisionContext
    empty_context = DecisionContext(
        ontology_version="v1",
        registry_policy_hashes=[],
        environment_constraints=[],
        optimizer_preferences={}
    )
    res = optimize_tree(tree_state.decision_graph, empty_context)
    
    trace = []
    for unc in evaluated_uncs:
        agent_unc = agent_uncs_map[unc.id]
        is_selected = (best_q is not None and best_q.uncertainty.id == unc.id)
        
        branch_generated = agent_unc.yes_candidate_architecture is not None and agent_unc.no_candidate_architecture is not None
        branch_feasible = (unc.yes_outcome.b_feasible if unc.yes_outcome else False) or (unc.no_outcome.b_feasible if unc.no_outcome else False)
        
        trace.append({
            "question_id": unc.id,
            "question_text": agent_unc.question_text,
            "impact_score": unc.decision_impact_score,
            "selected": is_selected,
            "user_answer": "N/A",
            "branch_generated": branch_generated,
            "branch_valid": True,
            "branch_feasible": branch_feasible,
            "branch_score": 0.0
        })

    if res.status == "CONTINUE" and best_q:
        return JourneyResponse(
            status="CONTINUE",
            selected_uncertainty_id=best_q.uncertainty.id,
            selected_uncertainty_text=best_q.question_text,
            selection_reason={
                "method": "impact_score",
                "score": best_q.uncertainty.decision_impact_score
            },
            exploration_trace=trace
        )
    else:
        best_score = 0.0
        if res.best_path_id:
            best_node = next((n for n in tree_state.decision_graph if n.id == res.best_path_id), None)
            best_score = best_node.path_score or 0.0 if best_node else 0.0
            
        return JourneyResponse(
            status=res.status,
            best_path_id=res.best_path_id,
            best_score=best_score,
            exploration_trace=trace
        )
