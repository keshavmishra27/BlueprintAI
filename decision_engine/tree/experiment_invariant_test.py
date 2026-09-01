import sys
from pathlib import Path
import json
import uuid

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement, UserIdea
from decision_engine.tree.tree_schemas import ProjectState, AgentUncertainty, StateMutation, TreeState, PathNode
from backend.app.routers.journey import start_journey, answer_journey, JourneyStartRequest, JourneyAnswerRequest, sessions

def run_invariant_test():
    print("==================================================")
    print(" END-TO-END INVARIANT TEST                        ")
    print("==================================================")
    
    session_id = str(uuid.uuid4())
    
    project_state = ProjectState(
        user_idea=UserIdea(
            what="Predict patient wait times",
            why="Hospitals are overcrowded",
            how_raw="",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        current_constraints=[],
        current_requirements=[Requirement(name="Low cost", required=True)]
    )
    
    v1_arch = ArchitectureNode(
        inputs=[], processing=["v1"], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=[], constraints=[]
    )
    
    uncertainty_u = AgentUncertainty(
        id="u1",
        question_text="Cloud or Local?",
        question_target="cloud",
        unknown_fact="Deployment environment",
        importance="High",
        yes_mutation=StateMutation(add_constraints=["cloud"], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=["local"], remove_constraints=[]),
        yes_candidate_architecture=ArchitectureNode(
            inputs=[], processing=["Hypothesis A (Cloud)"], decision=[], output=[], capabilities=[], 
            data_required=[], resources_required=["cloud"], constraints=[]
        ),
        no_candidate_architecture=ArchitectureNode(
            inputs=[], processing=["Hypothesis B (Local)"], decision=[], output=[], capabilities=[], 
            data_required=[], resources_required=["cpu"], constraints=[]
        )
    )
    
    print("\n--- POST /start ---")
    start_req = JourneyStartRequest(
        session_id=session_id,
        project_state=project_state,
        initial_architecture=v1_arch,
        candidate_uncertainties=[uncertainty_u]
    )
    res = start_journey(start_req)
    print(f"Status: {res.status}, Question: {res.selected_uncertainty_text}")
    
    print("\n--- User Selects YES ---")
    a1_arch = ArchitectureNode(
        inputs=[], processing=["A1 (Cloud Optimized)"], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=["cloud"], constraints=[]
    )
    
    tree = sessions[session_id]
    v1_node = tree.decision_graph[0]
    
    ans_req_yes = JourneyAnswerRequest(
        session_id=session_id,
        parent_node_id=v1_node.id,
        answer="YES",
        generated_architecture=a1_arch,
        candidate_uncertainties=[]
    )
    res2 = answer_journey(ans_req_yes)
    print(f"Status after YES: {res2.status}")
    
    a1_node = tree.decision_graph[-1]
    a1_node.path_value = 70.0 
    
    if res2.status == "CONTINUE":
        print("\n--- Engine demands we explore the NO branch! ---")
        b_node = next(n for n in tree.decision_graph if "Hypothesis B" in n.architecture.processing[0])
        
        b1_arch = ArchitectureNode(
            inputs=[], processing=["B1 (Local Optimized)"], decision=[], output=[], capabilities=[], 
            data_required=[], resources_required=["cpu"], constraints=[]
        )
        
        ans_req_no = JourneyAnswerRequest(
            session_id=session_id,
            parent_node_id=v1_node.id,
            answer="NO",
            generated_architecture=b1_arch,
            candidate_uncertainties=[]
        )
        res3 = answer_journey(ans_req_no)
        print(f"Status after NO: {res3.status}")
        
        b1_node = tree.decision_graph[-1]
        b1_node.path_value = 92.0
        
        from decision_engine.tree.optimizer import optimize_tree
        final_res = optimize_tree(tree.decision_graph, {'weight_cost': 0.5, 'weight_value': 0.5})
        print(f"Final Status: {final_res.status}, Best Path: {final_res.best_architecture.processing}")
    else:
        print("FAIL: The engine did not keep the unselected NO branch to explore!")

if __name__ == "__main__":
    run_invariant_test()
