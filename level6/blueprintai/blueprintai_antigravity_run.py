import sys
import uuid
import copy
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement, UserIdea
from decision_engine.tree.tree_schemas import ProjectState, AgentUncertainty, StateMutation
from backend.app.routers.journey import start_journey, answer_journey, get_journey_state, JourneyStartRequest, JourneyAnswerRequest

def run_blueprintai_protocol():
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
            "connectivity_strategy": "local intranet only",
            "input_modality": "database queries",
            "decision_mechanism": "XGBoost regression + rule-based thresholds"
        }
    )
    
    no_arch_db = copy.deepcopy(initial_arch)
    no_arch_db.inputs = ["daily CSV dump via USB or authorized manual transfer"]
    no_arch_db.processing = ["Local script processing CSV data daily", "Lightweight XGBoost model trained on historical data"]
    no_arch_db.capabilities = ["daily wait time prediction baseline", "overcrowding risk alerts (based on historical patterns)"]
    no_arch_db.architectural_decisions["input_modality"] = "manual CSV transfer"
    
    no_arch_ml = copy.deepcopy(initial_arch)
    no_arch_ml.processing = ["Simple statistical moving average (no ML training required)"]
    no_arch_ml.decision = ["Fixed rule-based thresholds"]
    no_arch_ml.architectural_decisions["decision_mechanism"] = "Statistical moving average"
    
    uncertainties = [
        AgentUncertainty(
            id=str(uuid.uuid4()),
            question_text="Do the existing hospital computers have permission to query the central hospital database directly?",
            question_target="Database access permissions",
            unknown_fact="Direct database query permissions",
            importance="High for data extraction strategy.",
            yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
            no_mutation=StateMutation(add_constraints=["no direct db connection"], remove_constraints=[]),
            yes_candidate_architecture=initial_arch,
            no_candidate_architecture=no_arch_db
        ),
        AgentUncertainty(
            id=str(uuid.uuid4()),
            question_text="Are the existing hospital computers powerful enough to train an ML model?",
            question_target="Local computing capacity",
            unknown_fact="Computing power of existing hospital computers",
            importance="Critical for determining if local ML training is feasible.",
            yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
            no_mutation=StateMutation(add_constraints=["no local ml training"], remove_constraints=[]),
            yes_candidate_architecture=initial_arch,
            no_candidate_architecture=no_arch_ml
        )
    ]
    
    session_id = str(uuid.uuid4())
    req = JourneyStartRequest(
        session_id=session_id,
        project_state=project_state,
        initial_architecture=initial_arch,
        candidate_uncertainties=uncertainties
    )
    
    print("=== STARTING BLUEPRINTAI RUN ===")
    resp = start_journey(req)
    print(f"Engine selected uncertainty: {resp.selected_uncertainty_text}")
    print("User answered: NO")
    
    agent_adapted_arch_for_no = copy.deepcopy(no_arch_db)
    
    state = get_journey_state(session_id)
    root_node = next(n for n in state.decision_graph if n.parent_id is None)
    
    print("\n=== ANSWERING 'NO' ===")
    ans_req = JourneyAnswerRequest(
        session_id=session_id,
        parent_node_id=root_node.id,
        answer="NO",
        generated_architecture=agent_adapted_arch_for_no,
        candidate_uncertainties=[],
        is_user_selected=True
    )
    ans_resp = answer_journey(ans_req)
    print(f"Status after NO answer: {ans_resp.status}")
    
    state = get_journey_state(session_id)
    unexplored = [n for n in state.decision_graph if n.status == "UNEXPLORED_HYPOTHESIS"]
    print(f"Unexplored hypotheses remaining: {len(unexplored)}")
    for n in unexplored:
        print(f" -> Exploring branch: '{n.user_answer}' for '{n.question_that_produced_it}'")
        
        agent_adapted_arch_for_yes = copy.deepcopy(initial_arch)
        
        yes_req = JourneyAnswerRequest(
            session_id=session_id,
            parent_node_id=n.parent_id,
            answer=n.user_answer,
            generated_architecture=agent_adapted_arch_for_yes,
            candidate_uncertainties=[],
            is_user_selected=False
        )
        yes_resp = answer_journey(yes_req)
        print(f"Status after {n.user_answer} answer: {yes_resp.status}")

    state = get_journey_state(session_id)
    terminals = [n for n in state.decision_graph if n.status in ["TERMINAL", "REJECTED", "ACTIVE"] and n.user_answer is not None]
    
    md_content = f"""# Run B: BlueprintAI Protocol Output

## 1. Initial Candidate Architectures Generated
- YES branch (Baseline logic): {initial_arch.processing[0]}
- NO branch (Adapted logic): {no_arch_db.processing[0]}

## 2. Python Selected Uncertainty
**{resp.selected_uncertainty_text}**

## 3. User Answer
**NO** (The existing hospital computers do not have permission to query the central hospital database directly).

## 4. Unexplored Hypotheses
The engine correctly identified that the **YES** branch remained an `UNEXPLORED_HYPOTHESIS` and forced the Agent to evaluate it for candidate space exhaustion.

## 5. Feasible Terminal Architectures Evaluated
"""
    for t in terminals:
        md_content += f"\n### Branch: {t.user_answer}\n"
        md_content += f"- **Feasible**: {t.path_value > 0}\n"
        md_content += f"- **PathScore**: {t.path_score}\n"
        md_content += f"- **Architecture**: {t.architecture.processing[0]}\n"
        
    best_id = yes_resp.best_path_id
    if not best_id and ans_resp.best_path_id:
        best_id = ans_resp.best_path_id
        
    best_node = next((n for n in state.decision_graph if n.id == best_id), None)
    
    md_content += f"\n## 6. Optimization Result\n"
    md_content += f"- **Best Architecture ID**: {best_id}\n"
    md_content += f"- **Selected Branch**: {best_node.user_answer if best_node else 'None'}\n"
    md_content += f"- **Was it selected by the User?**: {best_node.selected_by_user if best_node else False}\n"

    with open(Path(__file__).parent / "blueprintai_antigravity_run.md", "w") as f:
        f.write(md_content)
        
    print("\nSaved to blueprintai_antigravity_run.md")

if __name__ == "__main__":
    run_blueprintai_protocol()
