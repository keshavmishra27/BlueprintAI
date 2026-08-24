import sys
import json
import uuid
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement, UserIdea
from decision_engine.tree.tree_schemas import ProjectState, AgentUncertainty
from backend.app.routers.journey import start_journey, JourneyStartRequest

def run_b_start():
    idea = UserIdea(
        what="Predict patient waiting times and identify overcrowding before queues become critical.",
        why="Hospitals need earlier intervention without adding expensive infrastructure.",
        how_raw="AI-based prediction using historical queue, appointment, staffing and arrival data.",
        how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
    )
    initial_constraints = [
        "budget <= $500/month", 
        "no cloud infrastructure", 
        "existing hospital computers only", 
        "unreliable internet", 
        "30-day prototype", 
        "patient data must remain local"
    ]
    requirements = [
        Requirement(name="predict waiting time", required=True),
        Requirement(name="identify overcrowding risk", required=True),
        Requirement(name="useful accuracy", required=True),
        Requirement(name="low operating cost", required=True)
    ]
    
    project_state = ProjectState(
        user_idea=idea,
        current_constraints=initial_constraints,
        current_requirements=requirements
    )
    
    # My generated Initial Architecture for Run B (same as Baseline or slightly different)
    initial_arch = ArchitectureNode(
        inputs=["local hospital database (historical queue, appointments, staffing)"],
        processing=["Local cron job extracting data hourly", "Lightweight XGBoost model trained on historical data"],
        decision=["Threshold-based risk alert logic (e.g. queue > 10 and staffing < 3)"],
        output=["Local web dashboard accessible via hospital intranet"],
        capabilities=["hourly wait time prediction", "overcrowding risk alerts"],
        data_required=["historical queue data", "appointment data", "staffing data", "arrival data"],
        resources_required=["existing hospital computer", "local Python environment"],
        constraints=["budget <= $500/month", "no cloud infrastructure", "existing hospital computers only", "unreliable internet", "30-day prototype", "patient data must remain local"],
        evidence_provenance=[],
        architectural_decisions={
            "compute_location": "local existing hospital computer",
            "inference_strategy": "hourly batch prediction",
            "storage_location": "local hospital database",
            "connectivity_strategy": "local intranet only (airgapped from internet)",
            "input_modality": "database queries",
            "decision_mechanism": "XGBoost regression + rule-based thresholds",
            "human_approval": "dashboard alerts for staff review",
            "deployment_model": "local scripts via cron/task scheduler"
        }
    )
    
    # My generated uncertainties
    from decision_engine.tree.tree_schemas import StateMutation
    
    import copy
    no_arch_1 = copy.deepcopy(initial_arch)
    no_arch_1.processing = ["Simple statistical model (e.g. moving average)"]
    no_arch_1.decision = ["Fixed thresholds without ML logic"]
    
    no_arch_2 = copy.deepcopy(initial_arch)
    no_arch_2.inputs = ["daily CSV dump via USB or manual transfer"]
    no_arch_2.processing = ["Local script processing CSV data"]
    no_arch_2.architectural_decisions["input_modality"] = "CSV export"
    
    uncertainties = [
        AgentUncertainty(
            id=str(uuid.uuid4()),
            question_text="Are the existing hospital computers powerful enough to train an ML model?",
            question_target="Local computing capacity",
            unknown_fact="Computing power of existing hospital computers",
            importance="Critical for determining if local ML training is feasible.",
            yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
            no_mutation=StateMutation(add_constraints=["no local ml training"], remove_constraints=[]),
            yes_candidate_architecture=initial_arch,
            no_candidate_architecture=no_arch_1
        ),
        AgentUncertainty(
            id=str(uuid.uuid4()),
            question_text="Do the existing computers have permission to query the central hospital database directly?",
            question_target="Database access permissions",
            unknown_fact="Direct database query permissions",
            importance="High for data extraction strategy.",
            yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
            no_mutation=StateMutation(add_constraints=["no direct db connection"], remove_constraints=[]),
            yes_candidate_architecture=initial_arch,
            no_candidate_architecture=no_arch_2
        )
    ]
    
    session_id = str(uuid.uuid4())
    req = JourneyStartRequest(
        session_id=session_id,
        project_state=project_state,
        initial_architecture=initial_arch,
        candidate_uncertainties=uncertainties
    )
    
    resp = start_journey(req)
    
    print(f"Session ID: {session_id}")
    print(f"Status: {resp.status}")
    if resp.selected_uncertainty_text:
        print(f"Engine selected uncertainty: {resp.selected_uncertainty_text}")
        print(f"Selection reason: {resp.selection_reason}")
        print(f"Question to User: {resp.selected_uncertainty_text if resp.selected_uncertainty_text else 'None'}")

if __name__ == "__main__":
    run_b_start()
