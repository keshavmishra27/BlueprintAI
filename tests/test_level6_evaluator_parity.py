import sys
import uuid
from pathlib import Path
import json

base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from backend.app.routers.journey import (
    evaluate_architecture, EvaluateRequest,
    start_journey, JourneyStartRequest,
    sessions, JourneyStateResponse, get_journey_state
)
from decision_engine.input_layer.schemas import ArchitectureNode, UserIdea, Requirement
from decision_engine.tree.tree_schemas import ProjectState

def test_evaluator_parity():
    print("Running Evaluator Parity Test...\n")
    
    # 1. Setup identical scenario and architecture
    idea = UserIdea(
        what="Predict patient waiting times",
        why="Hospitals need earlier intervention",
        how_raw="AI-based prediction",
        how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
    )
    
    constraints = [
        "budget <= $500/month", 
        "no cloud infrastructure"
    ]
    
    requirements = [
        Requirement(name="predict waiting time", required=True),
        Requirement(name="low operating cost", required=True)
    ]
    
    project_state = ProjectState(
        user_idea=idea,
        current_constraints=constraints,
        current_requirements=requirements
    )
    
    arch = ArchitectureNode(
        inputs=["local hospital database"],
        processing=["Local cron job", "XGBoost"],
        decision=["Threshold logic"],
        output=["Local web dashboard"],
        capabilities=["prediction"],
        data_required=["historical data"],
        resources_required=["existing computer"],
        constraints=constraints,
        evidence_provenance=[],
        architectural_decisions={
            "compute_location": "local"
        }
    )
    
    # 2. Run Baseline (/api/journey/evaluate)
    req_eval = EvaluateRequest(
        project_state=project_state,
        architecture=arch
    )
    
    # Check session count before
    sessions_before = len(sessions)
    
    resp_eval = evaluate_architecture(req_eval)
    
    # Assert no mutation
    assert len(sessions) == sessions_before, "Baseline /evaluate mutated the global sessions store!"
    print("[OK] /api/journey/evaluate is pure and does not mutate journey state.")
    
    # 3. Run BlueprintAI (/api/journey/start)
    session_id = str(uuid.uuid4())
    req_start = JourneyStartRequest(
        session_id=session_id,
        project_state=project_state,
        initial_architecture=arch,
        candidate_uncertainties=[] # Empty to force immediate evaluation and completion
    )
    
    resp_start = start_journey(req_start)
    
    # Get the state to check the evaluation of the initial architecture
    state_resp = get_journey_state(session_id)
    
    # The root node in the tree corresponds to the initial architecture
    root_node = next((n for n in state_resp.decision_graph if n.parent_id is None), None)
    assert root_node is not None, "BlueprintAI tree missing root node"
    
    # 4. Compare Results
    # Evaluate endpoint feasible flag
    eval_feasible = resp_eval.feasible
    eval_req_met = resp_eval.requirements_met
    eval_cost = resp_eval.metrics.get('estimated_cost')
    
    # BlueprintAI tree node feasible flag
    # In journey.py, battle_history[0] is the root battle
    battle_result = state_resp.battle_history[0]
    bp_feasible = battle_result.b_feasible
    bp_req_met = sum(1 for r in battle_result.requirement_evaluations if r.player_b_satisfies)
    
    print(f"Baseline Feasible: {eval_feasible}")
    print(f"BlueprintAI Feasible: {bp_feasible}")
    assert eval_feasible == bp_feasible, "Feasibility mismatch between Baseline and BlueprintAI!"
    
    print(f"Baseline Requirements Met: {eval_req_met}")
    print(f"BlueprintAI Requirements Met: {bp_req_met}")
    assert eval_req_met == bp_req_met, "Requirements met mismatch between Baseline and BlueprintAI!"
    
    print("[OK] Feasibility and requirements evaluation matches exactly.")

if __name__ == "__main__":
    test_evaluator_parity()
