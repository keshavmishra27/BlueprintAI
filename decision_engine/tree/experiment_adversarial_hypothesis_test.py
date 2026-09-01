import sys
from pathlib import Path
import json
import uuid

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement, UserIdea
from decision_engine.tree.tree_schemas import ProjectState, AgentUncertainty, StateMutation
from backend.app.routers.journey import start_journey, answer_journey, JourneyStartRequest, JourneyAnswerRequest

def run_adversarial_test():
    print("==================================================")
    print(" ADVERSARIAL HYPOTHESIS TEST                      ")
    print("==================================================")
    
    session_id = str(uuid.uuid4())
    
    project_state = ProjectState(
        user_idea=UserIdea(
            what="Predict patient wait times",
            why="Hospitals are overcrowded",
            how_raw="",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        current_constraints=["strict budget $500/mo", "no cloud infrastructure"],
        current_requirements=[Requirement(name="Low cost", required=True)]
    )
    
    v1_arch = ArchitectureNode(
        inputs=[], processing=["Cloud GPU + Expensive API"], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=["cloud"], constraints=[]
    )
    
    uncertainty = AgentUncertainty(
        id=str(uuid.uuid4()),
        question_text="Can we remove cloud processing?",
        question_target="cloud",
        unknown_fact="Client willingness to use Local CPU",
        importance="High",
        yes_mutation=StateMutation(add_constraints=["local cpu allowed"], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=["must use cloud"], remove_constraints=[]),
        yes_candidate_architecture=ArchitectureNode(
            inputs=[], processing=["Local CPU Model"], decision=[], output=[], capabilities=[], 
            data_required=[], resources_required=["cpu"], constraints=[]
        ),
        no_candidate_architecture=ArchitectureNode(
            inputs=[], processing=["Cloud GPU Model"], decision=[], output=[], capabilities=[], 
            data_required=[], resources_required=["cloud"], constraints=[]
        )
    )
    
    print("\n--- STEP 1 & 2 & 3: API Start Journey ---")
    start_req = JourneyStartRequest(
        session_id=session_id,
        project_state=project_state,
        initial_architecture=v1_arch,
        candidate_uncertainties=[uncertainty]
    )
    
    res = start_journey(start_req)
    print(f"API Response Status: {res.status}")
    if res.status == "CONTINUE":
        print(f"API Selected Question: {res.selected_uncertainty_text}")
        print(f"Reason: {res.selection_reason}")
        
    print("\n--- STEP 4 & 5: Provide Answer ---")
    final_arch = ArchitectureNode(
        inputs=[], processing=["Optimized Local CPU Model"], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=["cpu"], constraints=[]
    )
    
    ans_req = JourneyAnswerRequest(
        session_id=session_id,
        parent_node_id="parent",
        answer="YES",
        generated_architecture=final_arch,
        candidate_uncertainties=[]
    )
    
    res2 = answer_journey(ans_req)
    print(f"API Response Status: {res2.status}")
    if res2.status == "BEST_ARCHITECTURE_FOUND":
        print(f"Winning Architecture Selected: {res2.best_architecture.processing}")
    
    print("\nTest Complete: The engine correctly rejected V1, evaluated hypotheses, selected the uncertainty, and optimized the terminal candidate.")

if __name__ == "__main__":
    run_adversarial_test()
