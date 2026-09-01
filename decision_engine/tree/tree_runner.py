import sys
from pathlib import Path
import copy

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement, UserIdea, ArchitectureComparison, Winner
from decision_engine.tree.tree_schemas import ArchitectureState, ProjectState, StateMutation, QuestionNode, TreeState, DecisionTraceEntry
from decision_engine.input_layer.evaluator import evaluate_battle
from decision_engine.tree.mock_llm import simulate_player_b_generation
from decision_engine.tree.question_generator import find_all_uncertainties, select_best_question
from decision_engine.tree.optimizer import optimize_tree, evaluate_node_state
from decision_engine.tree.tree_schemas import PathNode

class SimulatedUser:
    def __init__(self, constraint_profile: list[str]):
        self.constraint_profile = constraint_profile
        
    def answer_question(self, question: QuestionNode) -> str:
        for option_key, mutation in question.options.items():
            for constraint in mutation.add_constraints:
                if constraint in self.constraint_profile:
                    return option_key
        return "NO"

def main():
    print("==================================================")
    print("    ADAPTIVE TREE DECISION RUNNER                 ")
    print("==================================================\n")
    
    user_secret_profile = ["no historical data", "no gpu instance", "cloud infrastructure available"]
    simulated_user = SimulatedUser(user_secret_profile)
    
    idea = UserIdea(
        what="Reduce hospital waiting time",
        why="Patients wait too long.",
        how_raw="Maintain queue with LLM",
        how_structured=ArchitectureNode(
            inputs=["Patient appointment requests"],
            processing=["Maintain queue"],
            decision=["Simple rules for appointment time"],
            output=["Appointment schedule"],
            data_required=["Patient requests"],
            resources_required=["Local queue service", "Simple rules engine"],
            constraints=["Basic prediction limits"],
            capabilities=["queue management", "appointment prediction"]
        )
    )
    
    reqs = [
        Requirement(name="Reduce waiting time", required=True),
        Requirement(name="Handle resource bottlenecks", required=True)
    ]
    
    p_state = ProjectState(
        user_idea=idea,
        current_constraints=["cloud infrastructure available"], 
        current_requirements=reqs
    )
    
    user_arch_state = ArchitectureState(
        architecture=idea.how_structured,
        generation=1,
        based_on="User original input"
    )
    
    b_arch_state = simulate_player_b_generation(1, p_state)
    
    print(">>> LEVEL 0: Initial State")
    print(f"Constraints: {p_state.current_constraints}")
    result_0 = evaluate_battle(user_arch_state.architecture, b_arch_state.architecture, p_state.current_constraints, p_state.current_requirements)
    print(f"User Feasible: {result_0.a_feasible} | Player B Feasible: {result_0.b_feasible}")
    print(f"Winner: {result_0.winner.value.upper()}\n")
    
    tree_state = TreeState(
        current_state_id="level_0",
        project_state=p_state,
        user_architecture=user_arch_state,
        player_b_architecture=b_arch_state,
        battle_history=[result_0]
    )
    
    decision_trace = []
    
    depth = 0
    MAX_DEPTH = 3
    
    while depth < MAX_DEPTH:
        depth += 1
        print(f"\n==================================================")
        print(f"                 LEVEL {depth}                    ")
        print(f"==================================================")
        
        uncertainties = find_all_uncertainties(tree_state.player_b_architecture, tree_state.user_architecture, tree_state.project_state)
        
        if not uncertainties:
            print("\n[STOP] No unresolved uncertainties found.")
            break
            
        q_node = select_best_question(uncertainties)
        
        if not q_node or q_node.uncertainty.decision_impact_score == 0:
            print("\n[STOP] No candidate questions have meaningful decision impact.")
            break
            
        print(f"\n>>> QUESTION NODE: {q_node.question_text}")
        
        user_answer = simulated_user.answer_question(q_node)
        print(f"\nUser selects: {user_answer}")
        
        mutation = q_node.options[user_answer]
        
        new_constraints = [c for c in mutation.add_constraints if c not in tree_state.project_state.current_constraints]
        if not new_constraints:
            print("\n[STOP] State mutation produces no state change.")
            break
            
        trace_entry = DecisionTraceEntry(
            question_text=q_node.question_text,
            why_selected=f"YES -> {q_node.uncertainty.yes_outcome.architecture_name} ({q_node.uncertainty.yes_outcome.winner}), NO -> {q_node.uncertainty.no_outcome.architecture_name} ({q_node.uncertainty.no_outcome.winner}). Impact={q_node.uncertainty.decision_impact_score}",
            user_answer=user_answer,
            state_mutation=mutation.add_constraints,
            architecture_before=" -> ".join(tree_state.player_b_architecture.architecture.processing),
            architecture_after="",
            battle_before=tree_state.battle_history[-1].winner.value,
            battle_after=""
        )
        
        tree_state.project_state.current_constraints.extend(new_constraints)
        
        print("\n[Player B Adapting...]")
        new_b_arch_state = simulate_player_b_generation(tree_state.player_b_architecture.generation + 1, tree_state.project_state)
        tree_state.player_b_architecture = new_b_arch_state
        
        print(f"Player B generates v{tree_state.player_b_architecture.generation}")
        if tree_state.player_b_architecture.based_on:
            print(f"Reasoning: {tree_state.player_b_architecture.based_on}")
            
        trace_entry.architecture_after = " -> ".join(tree_state.player_b_architecture.architecture.processing)
            
        new_result = evaluate_battle(
            tree_state.user_architecture.architecture, 
            tree_state.player_b_architecture.architecture, 
            tree_state.project_state.current_constraints, 
            tree_state.project_state.current_requirements
        )
        tree_state.battle_history.append(new_result)
        trace_entry.battle_after = new_result.winner.value
        
        print(f"\n[Post-Adaptation Evaluation]")
        print(f"Player B v{tree_state.player_b_architecture.generation} Feasible: {new_result.b_feasible}")
        print(f"Winner: {new_result.winner.value.upper()}")
        
        decision_trace.append(trace_entry)
        
    print("\n==================================================")
    print("                  TREE RUN COMPLETE               ")
    print("==================================================")
    
    print("\n--- FINAL ARCHITECTURE ---")
    print(f"Player B v{tree_state.player_b_architecture.generation}")
    print(f"Processing: {' -> '.join(tree_state.player_b_architecture.architecture.processing)}")
    print(f"Constraints: {tree_state.project_state.current_constraints}")
    print(f"Final Winner: {tree_state.battle_history[-1].winner.value.upper()}")
    
    print("\n--- OPTIMIZATION RESULTS ---")
    mock_graph = []
    mock_graph.append(PathNode(
        id="final_chosen",
        parent_id="root",
        architecture=tree_state.player_b_architecture.architecture,
        status=evaluate_node_state(None, is_leaf=True, has_unknowns=False, passes_hard_gates=tree_state.battle_history[-1].b_feasible),
        selected_by_user=True,
        path_cost=100.0,
        path_value=90.0
    ))
    
    from decision_engine.input_layer.schemas import ArchitectureNode
    alt_arch = ArchitectureNode(
        inputs=[], processing=["Unselected Fast Path"], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[]
    )
    mock_graph.append(PathNode(
        id="alt_unselected",
        parent_id="root",
        architecture=alt_arch,
        status="TERMINAL",
        selected_by_user=False,
        path_cost=50.0,
        path_value=95.0
    ))
    
    tree_state.decision_graph = mock_graph
    
    res = optimize_tree(tree_state.decision_graph, {'weight_cost': 0.5, 'weight_value': 0.5})
    print(f"Status: {res.status}")
    if res.best_path_id:
        print(f"Best Path ID: {res.best_path_id}")
        best_node = next(n for n in tree_state.decision_graph if n.id == res.best_path_id)
        print(f"Selected by user? {best_node.selected_by_user}")
        if best_node.architecture:
            print(f"Best Architecture: {' -> '.join(best_node.architecture.processing)}")
    
    print("\n--- DECISION TRACE ---")
    for i, step in enumerate(decision_trace, 1):
        print(f"\nSTEP {i}:")
        print(f"QUESTION: {step.question_text}")
        print(f"WHY SELECTED: {step.why_selected}")
        print(f"USER: {step.user_answer}")
        print(f"STATE CHANGE: {step.state_mutation}")
        print(f"ARCHITECTURE: {step.architecture_before} \n           -> {step.architecture_after}")
        print(f"BATTLE: {step.battle_before.upper()} -> {step.battle_after.upper()}")

if __name__ == "__main__":
    main()
