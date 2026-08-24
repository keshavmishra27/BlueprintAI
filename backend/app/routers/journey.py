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

from benchmark_suite.schemas import BenchmarkScenario
from decision_engine.tree.benchmark_evaluator import (
    evaluate_architecture_metrics,
    compute_s_abs,
    DeterministicEvaluationRules,
    OptimizationWeights,
    ScoringAnchors
)

router = APIRouter(prefix="/api/journey", tags=["journey"])

# In-memory session store for TreeState (for this experimental phase)
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
    answer: str  # "YES" or "NO"
    generated_architecture: ArchitectureNode
    candidate_uncertainties: List[AgentUncertainty]
    is_user_selected: bool = False

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
    # Evaluate feasibility and requirements
    battle_result = evaluate_battle(
        req.architecture, # We use the same for both sides to just test absolute feasibility
        req.architecture,
        req.project_state.current_constraints,
        req.project_state.current_requirements
    )
    
    # Scenario-driven evaluation / metrics
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
        
    # Initialize the project state
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
    
    # Evaluate the initial battle
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
        battle_history=[battle_result],
        decision_graph=[]
    )
    sessions[req.session_id] = tree_state
    
    # Evaluate uncertainties
    evaluated_uncs = evaluate_provided_uncertainties(
        req.candidate_uncertainties,
        b_arch_state,
        user_arch_state,
        p_state
    )
    
    # Check if there are uncertainties to resolve
    agent_uncs_map = {u.id: u for u in req.candidate_uncertainties}
    best_q = select_best_question(evaluated_uncs, agent_uncs_map)
    
    root_node_id = str(uuid.uuid4())
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
    s_abs = compute_s_abs(
        battle_result.b_feasible, 
        root_metrics["estimated_value"], 
        root_metrics["estimated_cost"], 
        root_metrics["estimated_latency_ms"], 
        root_metrics["estimated_timeline_days"], 
        anchors, 
        weights
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
        reject_reasons=battle_result.b_constraint_violations,
        selected_by_user=True
    )
    tree_state.decision_graph.append(root_node)
    
    if best_q:
        # Add the hypothesis branches as NEEDS_INFORMATION nodes
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
            "user_answer": "N/A",  # Set by agent_driver if selected
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
        # Search is immediately exhausted (no uncertainties proposed or zero impact)
        res = optimize_tree(tree_state.decision_graph, {})
        return JourneyResponse(
            status=res.status,
            best_path_id=res.best_path_id,
            best_score=0.0, # calculate if needed
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
    
    battle_result = evaluate_battle(
        tree_state.user_architecture.architecture, 
        b_arch_state.architecture, 
        tree_state.project_state.current_constraints, 
        tree_state.project_state.current_requirements
    )
    tree_state.battle_history.append(battle_result)
    
    # Evaluate new uncertainties
    evaluated_uncs = evaluate_provided_uncertainties(
        req.candidate_uncertainties,
        b_arch_state,
        tree_state.user_architecture,
        tree_state.project_state
    )
    
    agent_uncs_map = {u.id: u for u in req.candidate_uncertainties}
    best_q = select_best_question(evaluated_uncs, agent_uncs_map)
    
    new_node_id = str(uuid.uuid4())
    node_status = evaluate_node_state(
        None, 
        is_leaf=True, 
        has_unknowns=bool(best_q), 
        passes_hard_gates=battle_result.b_feasible
    )
    
    if parent_node:
        parent_node.status = "ACTIVE" # parent is no longer leaf
        
    priv = private_sessions.get(req.session_id)
    rules = priv.evaluation_rules if priv else DeterministicEvaluationRules()
    weights = priv.optimization_weights if priv else OptimizationWeights(w_value=0.5, w_cost=0.5, w_performance=0.0, w_timeline=0.0)
    anchors = priv.scoring_anchors if priv else ScoringAnchors(value_maximum=100.0, cost_budget_limit=1000.0, latency_target_ms=100.0, timeline_maximum_days=10.0)
    
    new_metrics = evaluate_architecture_metrics(b_arch_state.architecture, rules)
    s_abs = compute_s_abs(
        battle_result.b_feasible, 
        new_metrics["estimated_value"], 
        new_metrics["estimated_cost"], 
        new_metrics["estimated_latency_ms"], 
        new_metrics["estimated_timeline_days"], 
        anchors, 
        weights
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
        reject_reasons=battle_result.b_constraint_violations,
        selected_by_user=req.is_user_selected,
        user_answer=req.answer
    )
    
    # If the user answered a question, there should be a placeholder hypothesis node. We remove it and replace it with this real node.
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
                user_answer=option_key
            )
            tree_state.decision_graph.append(hypo_node)
    
    res = optimize_tree(tree_state.decision_graph, {})
    
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
            "user_answer": "N/A",  # Set by agent_driver if selected
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
