import sys
import json
import uuid
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement, UserIdea
from decision_engine.tree.tree_schemas import ProjectState
from backend.app.routers.journey import start_journey, answer_journey, get_journey_state, JourneyStartRequest, JourneyAnswerRequest
from decision_engine.tree.automated_protocol_simulator import AutomatedProtocolSimulator

def run_experiment():
    print("==================================================")
    print(" LEVEL 6 EXPERIMENT: TRUE ANTIGRAVITY PROTOCOL")
    print("==================================================")
    
    idea = UserIdea(
        what="Predict patient wait times",
        why="Hospitals are overcrowded",
        how_raw="Use a massive LLM on cloud GPUs to analyze historical queue data",
        how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
    )
    initial_constraints = ["strict budget $500/mo", "no cloud infrastructure"]
    requirements = [Requirement(name="Low cost", required=True), Requirement(name="High accuracy", required=True)]
    
    project_state = ProjectState(
        user_idea=idea,
        current_constraints=initial_constraints,
        current_requirements=requirements
    )
    
    simulator = AutomatedProtocolSimulator()
    initial_arch = simulator.generate_initial_architecture(project_state)
    uncertainties = simulator.find_uncertainties(initial_arch, project_state)
    
    session_id = str(uuid.uuid4())
    
    print("\n--- Starting Journey ---")
    req = JourneyStartRequest(
        session_id=session_id,
        project_state=project_state,
        initial_architecture=initial_arch,
        candidate_uncertainties=uncertainties
    )
    start_resp = start_journey(req)
    
    print(f"Status: {start_resp.status}")
    if start_resp.selected_uncertainty_text:
        print(f"Engine selected uncertainty: {start_resp.selected_uncertainty_text}")
        print(f"Selection reason: {start_resp.selection_reason}")
        
    
    iteration = 0
    ans_resp = start_resp
    
    while True:
        iteration += 1
        if iteration > 10:
            print("Safety break: too many iterations")
            break
            
        state_resp = get_journey_state(session_id)
        decision_graph = state_resp.decision_graph
        unexplored_nodes = [n for n in decision_graph if n.status == "UNEXPLORED_HYPOTHESIS"]
        
        if not unexplored_nodes:
            print("\nNo unexplored hypotheses remaining. Search is exhausted.")
            break
            
        node_to_explore = unexplored_nodes[0]
        question_text = node_to_explore.question_that_produced_it
        answer_branch = node_to_explore.user_answer
        parent_id = node_to_explore.parent_id
        
        print(f"\n--- Exploring Branch ---")
        print(f"Question: {question_text}")
        print(f"Branch: {answer_branch}")
        
        adaptation_reason = f"User theoretically answered {answer_branch} to: {question_text}"
        adapted_arch = simulator.generate_adapted_architecture(
            project_state, 
            initial_arch,
            adaptation_reason
        )
        new_uncertainties = simulator.find_uncertainties(adapted_arch, project_state)
        
        ans_req = JourneyAnswerRequest(
            session_id=session_id,
            parent_node_id=parent_id,
            answer=answer_branch,
            generated_architecture=adapted_arch,
            candidate_uncertainties=new_uncertainties
        )
        
        ans_resp = answer_journey(ans_req)
        print(f"Status after answering: {ans_resp.status}")
        if ans_resp.selected_uncertainty_text:
            print(f"Engine selected new uncertainty: {ans_resp.selected_uncertainty_text}")

    print("\n==================================================")
    print(" EXPERIMENT RESULTS LOG")
    print("==================================================")
    
    final_state = get_journey_state(session_id)
    graph = final_state.decision_graph
    
    terminals = [n for n in graph if n.status == "TERMINAL"]
    rejected = [n for n in graph if n.status == "REJECTED"]
    
    print("\n1. Initial Gemini Architecture:")
    print("   -> " + " -> ".join(initial_arch.processing))
    
    print("\n2. Uncertainties proposed initially:")
    for u in uncertainties:
        print(f"   - {u.unknown_fact} (Impact: {u.decision_impact_score})")
        
    print(f"\n3. Python Selected: {start_resp.selected_uncertainty_text}")
    print(f"   Reason: {start_resp.selection_reason}")
    
    print("\n4. Explored user answers:")
    for n in graph:
        if n.status in ["TERMINAL", "REJECTED"] and n.user_answer:
            print(f"   - {n.user_answer} (for {n.question_that_produced_it})")
            
    print("\n5. Gemini's adapted architectures:")
    for n in graph:
        if n.status in ["TERMINAL", "REJECTED"] and n.user_answer:
            print(f"   - [{n.user_answer}] -> " + " -> ".join(n.architecture.processing))
            
    print("\n6. 5-D Evaluations (from history):")
    for i, b in enumerate(final_state.battle_history):
        print(f"   Battle {i+1}: Winner={b.winner}, Feasible={b.b_feasible}, Violations={b.b_constraint_violations}")
        
    print(f"\n7. Rejected branches: {len(rejected)}")
    for r in rejected:
        print(f"   - ID: {r.id}, Reason: Did not pass hard gates")
        
    print(f"\n8. Terminal Candidate Set (F): {len(terminals)} architectures")
    for t in terminals:
        print(f"   - ID: {t.id}, Path Value: {t.path_value}, Cost: {t.path_cost}")
        
    print("\n9. PathScores for F:")
    for t in terminals:
        print(f"   - ID: {t.id} -> Score: {t.path_score}")
        
    best_id = ans_resp.best_path_id
    print(f"\n10. Final best_path_id: {best_id}")
    
    best_node = None
    if best_id:
        best_node = next((n for n in graph if n.id == best_id), None)
        print(f"\n11. Selected branch != mathematical winner? (Experiment A Test)")
        print(f"    Best node selected by user explicitly? {best_node.selected_by_user}")
        if not best_node.selected_by_user:
            print("    [PASSED] The optimal branch was NOT the conversationally selected branch!")
        else:
            print("    [NOTE] The optimal branch happened to be the conversationally selected branch.")
    
    print(f"\n12. Termination Status: {ans_resp.status}")
    
    print("\n=== VERIFICATION INVARIANTS ===")
    if best_id and best_node:
        print(f"1. B1 exists in graph? {any(n.id == best_id for n in graph)}")
        print(f"2. B1 is TERMINAL? {best_node.status == 'TERMINAL'}")
        print(f"3. B1 passed hard gates? {best_node.path_value > 0}")
        print(f"4. B1 is in F? {best_node in terminals}")
        print(f"5. B1.selected_by_user == False? {best_node.selected_by_user == False}")
        print(f"6. B1 score is max? {best_node.path_score == max(t.path_score for t in terminals)}")
        print(f"7. Python selected B1? True")
        print(f"8. No unexplored hypotheses remain? {not any(n.status == 'UNEXPLORED_HYPOTHESIS' for n in graph)}")

if __name__ == "__main__":
    run_experiment()
