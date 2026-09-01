from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import uuid

from .models import (
    IdeaAnalyzeRequest, Decision, RepoAnalyzeRequest, GapReport,
    RefinementCreateRequest, RefinementCreateResponse, RefinementApplyRequest,
    DecisionStatusUpdateRequest
)
from .journey_models import (
    StartJourneyRequest, JourneyStepResponse, AnswerQuestionRequest
)
from product.db.session import get_db
from product.service import ProductService
from product.journey_service import JourneyService, serialize_pydantic_obj

router = APIRouter()

_journey_sessions = {}

def get_product_service(db: Session = Depends(get_db)):
    return ProductService(db)

def get_journey_service():
    return JourneyService()

@router.post("/ideas/analyze", response_model=Decision)
def analyze_idea(request: IdeaAnalyzeRequest, service: ProductService = Depends(get_product_service)):
    decision = service.analyze_idea(request.idea, request.context)
    return decision

@router.post("/journey/start", response_model=JourneyStepResponse)
def start_journey(req: StartJourneyRequest, 
                  j_service: JourneyService = Depends(get_journey_service),
                  p_service: ProductService = Depends(get_product_service)):
    result = j_service.start_journey(
        req.what, req.why, req.how, 
        req.constraints, req.requirements, 
        req.gemini_baseline_architecture, 
        req.player_b_architecture, 
        req.uncertainties,
        req.optimization_preferences
    )
    
    session_id = str(uuid.uuid4())
    tree_state = result["tree_state"]
    q_node = result["current_question"]
    
    _journey_sessions[session_id] = {
        "status": "active" if not result["is_complete"] else "complete",
        "current_depth": 0,
        "project_state_json": tree_state.project_state.model_dump_json(),
        "user_architecture_json": tree_state.user_architecture.model_dump_json(),
        "player_b_architecture_json": tree_state.player_b_architecture.model_dump_json(),
        "battle_history_json": json.dumps([serialize_pydantic_obj(b) for b in tree_state.battle_history]),
        "decision_trace_json": json.dumps([]),
        "current_question_json": q_node.model_dump_json() if q_node else None,
        "what": req.what,
        "why": req.why,
    }
    
    response = JourneyStepResponse(
        session_id=session_id,
        is_complete=result["is_complete"],
        current_architecture=serialize_pydantic_obj(tree_state.player_b_architecture.architecture),
        current_constraints=tree_state.project_state.current_constraints,
        current_requirements=[serialize_pydantic_obj(r) for r in tree_state.project_state.current_requirements],
        current_battle_result=serialize_pydantic_obj(tree_state.battle_history[-1]),
        current_question=serialize_pydantic_obj(q_node),
        decision_impact=q_node.uncertainty.decision_impact_score if q_node else None,
        trace_so_far=[],
        decision_graph=[serialize_pydantic_obj(n) for n in tree_state.decision_graph],
        best_path_id=result.get("best_path_id"),
        final_architecture=None
    )
    
    if result["is_complete"]:
        idea_text = f"What: {req.what} Why: {req.why}"
        context = {"architecture": serialize_pydantic_obj(tree_state.player_b_architecture.architecture)}
        decision = p_service.analyze_idea(idea_text, context)
        response.final_architecture = serialize_pydantic_obj(tree_state.player_b_architecture.architecture)
        response.decision_id = decision.id
        response.decision_fingerprint = decision.decision_fingerprint
        
    return response

@router.post("/journey/answer", response_model=JourneyStepResponse)
def answer_journey(req: AnswerQuestionRequest, 
                   j_service: JourneyService = Depends(get_journey_service),
                   p_service: ProductService = Depends(get_product_service)):
    if req.session_id not in _journey_sessions:
        raise HTTPException(status_code=404, detail="Journey not found")
        
    j_data = _journey_sessions[req.session_id]
    if j_data["status"] == "complete":
        raise HTTPException(status_code=400, detail="Journey already complete")
        
    from decision_engine.tree.tree_schemas import ProjectState, ArchitectureState, TreeState, DecisionTraceEntry, QuestionNode
    from decision_engine.input_layer.schemas import ArchitectureComparison
    
    p_state = ProjectState.model_validate_json(j_data["project_state_json"])
    u_arch = ArchitectureState.model_validate_json(j_data["user_architecture_json"])
    b_arch = ArchitectureState.model_validate_json(j_data["player_b_architecture_json"])
    battle_list = [ArchitectureComparison.model_validate(b) for b in json.loads(j_data["battle_history_json"])]
    trace_list = [DecisionTraceEntry.model_validate(t) for t in json.loads(j_data["decision_trace_json"])]
    current_q_node = QuestionNode.model_validate_json(j_data["current_question_json"]) if j_data["current_question_json"] else None
    
    if not current_q_node:
        raise HTTPException(status_code=400, detail="No active question to answer")
        
    tree_state = TreeState(
        current_state_id=f"level_{j_data['current_depth']}",
        project_state=p_state,
        user_architecture=u_arch,
        player_b_architecture=b_arch,
        battle_history=battle_list
    )
    
    try:
        result = j_service.answer_question(
            tree_state, current_q_node, 
            req.selected_option, 
            req.new_player_b_architecture, 
            req.new_uncertainties
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    new_tree_state = result["tree_state"]
    next_q_node = result["current_question"]
    trace_entry = result["trace_entry"]
    
    trace_list.append(trace_entry)
    
    j_data["status"] = "active" if not result["is_complete"] else "complete"
    j_data["current_depth"] += 1
    j_data["project_state_json"] = new_tree_state.project_state.model_dump_json()
    j_data["user_architecture_json"] = new_tree_state.user_architecture.model_dump_json()
    j_data["player_b_architecture_json"] = new_tree_state.player_b_architecture.model_dump_json()
    j_data["battle_history_json"] = json.dumps([serialize_pydantic_obj(b) for b in new_tree_state.battle_history])
    j_data["decision_trace_json"] = json.dumps([serialize_pydantic_obj(t) for t in trace_list])
    j_data["current_question_json"] = next_q_node.model_dump_json() if next_q_node else None
    
    response = JourneyStepResponse(
        session_id=req.session_id,
        is_complete=result["is_complete"],
        current_architecture=serialize_pydantic_obj(new_tree_state.player_b_architecture.architecture),
        current_constraints=new_tree_state.project_state.current_constraints,
        current_requirements=[serialize_pydantic_obj(r) for r in new_tree_state.project_state.current_requirements],
        current_battle_result=serialize_pydantic_obj(new_tree_state.battle_history[-1]),
        current_question=serialize_pydantic_obj(next_q_node),
        decision_impact=next_q_node.uncertainty.decision_impact_score if next_q_node else None,
        trace_so_far=[serialize_pydantic_obj(t) for t in trace_list],
        decision_graph=[serialize_pydantic_obj(n) for n in new_tree_state.decision_graph],
        best_path_id=result.get("best_path_id"),
        final_architecture=None
    )

    if result["is_complete"]:
        idea_text = f"What: {j_data['what']} Why: {j_data['why']}"
        context = {"architecture": serialize_pydantic_obj(new_tree_state.player_b_architecture.architecture)}
        decision = p_service.analyze_idea(idea_text, context)
        response.final_architecture = serialize_pydantic_obj(new_tree_state.player_b_architecture.architecture)
        response.decision_id = decision.id
        response.decision_fingerprint = decision.decision_fingerprint
        
    return response

@router.get("/journey/{session_id}", response_model=JourneyStepResponse)
def get_journey(session_id: str):
    if session_id not in _journey_sessions:
        raise HTTPException(status_code=404, detail="Journey not found")
        
    j_data = _journey_sessions[session_id]
    
    from decision_engine.tree.tree_schemas import ProjectState, ArchitectureState, QuestionNode, DecisionTraceEntry
    from decision_engine.input_layer.schemas import ArchitectureComparison
    
    p_state = ProjectState.model_validate_json(j_data["project_state_json"])
    b_arch = ArchitectureState.model_validate_json(j_data["player_b_architecture_json"])
    battle_list = [ArchitectureComparison.model_validate(b) for b in json.loads(j_data["battle_history_json"])]
    trace_list = [DecisionTraceEntry.model_validate(t) for t in json.loads(j_data["decision_trace_json"])]
    current_q_node = QuestionNode.model_validate_json(j_data["current_question_json"]) if j_data["current_question_json"] else None
    
    is_complete = j_data["status"] == "complete"
    
    return JourneyStepResponse(
        session_id=session_id,
        is_complete=is_complete,
        current_architecture=serialize_pydantic_obj(b_arch.architecture),
        current_constraints=p_state.current_constraints,
        current_requirements=[serialize_pydantic_obj(r) for r in p_state.current_requirements],
        current_battle_result=serialize_pydantic_obj(battle_list[-1]) if battle_list else None,
        current_question=serialize_pydantic_obj(current_q_node),
        decision_impact=current_q_node.uncertainty.decision_impact_score if current_q_node else None,
        trace_so_far=[serialize_pydantic_obj(t) for t in trace_list],
        final_architecture=serialize_pydantic_obj(b_arch.architecture) if is_complete else None
    )

@router.post("/repositories/analyze", response_model=GapReport)
def analyze_repository(request: RepoAnalyzeRequest, service: ProductService = Depends(get_product_service)):
    try:
        gap_report = service.analyze_repository(request.decision_id, request.repo_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    if not gap_report:
        raise HTTPException(status_code=404, detail="Decision not found or analysis failed")
    return gap_report

@router.post("/refinements/create", response_model=RefinementCreateResponse)
def create_refinement_options(request: RefinementCreateRequest, service: ProductService = Depends(get_product_service)):
    options = service.create_refinement_options(request.decision_id, request.gap_report_id, request.new_constraint)
    return RefinementCreateResponse(options=options)

@router.post("/refinements/apply", response_model=Decision)
def apply_refinement(request: RefinementApplyRequest, service: ProductService = Depends(get_product_service)):
    decision = service.apply_refinement(
        request.decision_id, 
        request.gap_report_id, 
        request.applied_exploration, 
        request.preserved,
        request.problem_detected
    )
    if not decision:
        raise HTTPException(status_code=404, detail="Refinement failed")
    return decision

@router.get("/decisions/{decision_id}", response_model=Decision)
def get_decision(decision_id: str, service: ProductService = Depends(get_product_service)):
    decision = service.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision

@router.get("/decisions/{decision_id}/history", response_model=List[Decision])
def get_decision_history(decision_id: str, service: ProductService = Depends(get_product_service)):
    history = service.get_decision_history(decision_id)
    if not history:
        raise HTTPException(status_code=404, detail="Decision not found")
    return history

@router.get("/decisions/{decision_id}/lineage", response_model=List[Decision])
def get_decision_lineage(decision_id: str, service: ProductService = Depends(get_product_service)):
    lineage = service.get_decision_history(decision_id)
    if not lineage:
        raise HTTPException(status_code=404, detail="Decision not found")
    return lineage

@router.get("/decisions/{decision_id}/children", response_model=List[Decision])
def get_decision_children(decision_id: str, service: ProductService = Depends(get_product_service)):
    decision = service.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return service.get_decision_children(decision_id)

@router.patch("/decisions/{decision_id}/status", response_model=Decision)
def update_decision_status(
    decision_id: str, 
    request: DecisionStatusUpdateRequest, 
    service: ProductService = Depends(get_product_service)
):
    if request.status not in ["ACTIVE", "SUPERSEDED", "REVOKED"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    decision = service.update_decision_status(decision_id, request.status)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision

@router.get("/decisions", response_model=List[Decision])
def get_decisions(
    limit: int = 10, 
    root_decision_id: str = None,
    status: str = None,
    service: ProductService = Depends(get_product_service)
):
    if root_decision_id:
        return service.get_decisions_by_root(root_decision_id, status)
    
    decisions = service.get_recent_decisions(limit)
    if status:
        decisions = [d for d in decisions if d.status == status]
    return decisions
