import sys
from pathlib import Path
import json
import uuid

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement, UserIdea
from decision_engine.tree.tree_schemas import ProjectState, AgentUncertainty, StateMutation
from decision_engine.tree.experiment_llm_adapters import llm_baseline, llm_generate_player_b
from backend.app.routers.journey import start_journey, answer_journey, JourneyStartRequest, JourneyAnswerRequest, sessions

def mock_agent_generate_uncertainties() -> list[AgentUncertainty]:
    return [
        AgentUncertainty(
            id=str(uuid.uuid4()),
            question_text="Is cloud infrastructure available?",
            question_target="cloud_infrastructure",
            unknown_fact="Availability of Cloud Infrastructure",
            importance="High",
            yes_mutation=StateMutation(add_constraints=["cloud infrastructure available"], remove_constraints=[]),
            no_mutation=StateMutation(add_constraints=["no cloud infrastructure"], remove_constraints=[]),
            yes_candidate_architecture=ArchitectureNode(
                inputs=[], processing=["Cloud Pipeline"], decision=[], output=[], capabilities=[], data_required=[], resources_required=["cloud"], constraints=[]
            ),
            no_candidate_architecture=ArchitectureNode(
                inputs=[], processing=["Local Server Pipeline"], decision=[], output=[], capabilities=[], data_required=[], resources_required=["cpu"], constraints=[]
            )
        )
    ]

MESSY_SCENARIOS = [
    {
        "name": "Budget Constrained Healthcare",
        "idea": UserIdea(
            what="Predict patient wait times",
            why="Hospitals are overcrowded",
            how_raw="Use a massive LLM on cloud GPUs to analyze historical queue data",
            how_structured=ArchitectureNode(
                inputs=[], processing=["Massive Cloud LLM"], decision=[], output=[], capabilities=[], data_required=["historical data"], resources_required=["cloud", "gpu"], constraints=[]
            )
        ),
        "initial_constraints": ["strict budget $500/mo"],
        "simulated_user_profile": ["no gpu instance", "cloud infrastructure available", "historical data available"],
        "requirements": [Requirement(name="Low cost", required=True), Requirement(name="High accuracy", required=True)]
    },
]

def run_experiment():
    print("==================================================")
    print(" EXPERIMENT MODE A: GEMINI API BASELINE           ")
    print("==================================================")
    
    results = []
    
    for i, scenario in enumerate(MESSY_SCENARIOS):
        print(f"\nRunning Scenario {i+1}: {scenario['name']}")
        
        print("  [Baseline] Running single-shot Gemini...")
        baseline_arch = llm_baseline(scenario['idea'], scenario['initial_constraints'])
        
        from decision_engine.input_layer.evaluator import evaluate_battle
        baseline_battle = evaluate_battle(
            scenario['idea'].how_structured,
            baseline_arch,
            scenario['initial_constraints'],
            scenario['requirements']
        )
        
        baseline_feasible = baseline_battle.b_feasible
        baseline_reqs = sum(1 for r in baseline_battle.requirement_evaluations if r.player_b_satisfies)
        
        print(f"    Baseline Feasible: {baseline_feasible}")
        
        print("  [BlueprintAI] Running through API protocol...")
        session_id = str(uuid.uuid4())
        
        project_state = ProjectState(
            user_idea=scenario['idea'],
            current_constraints=scenario['initial_constraints'].copy(),
            current_requirements=scenario['requirements']
        )
        
        agent_arch_response = llm_generate_player_b(project_state, "No previous evidence")
        candidate_uncertainties = mock_agent_generate_uncertainties()
        
        start_req = JourneyStartRequest(
            session_id=session_id,
            project_state=project_state,
            initial_architecture=agent_arch_response.architecture,
            candidate_uncertainties=candidate_uncertainties
        )
        api_res = start_journey(start_req)
        
        loop_count = 0
        while api_res.status == "CONTINUE" and loop_count < 3:
            loop_count += 1
            print(f"    API asked: {api_res.selected_uncertainty_text}")
            
            user_answer = "YES"
            
            adapted_arch = llm_generate_player_b(project_state, "Adapted for NO branch")
            
            answer_req = JourneyAnswerRequest(
                session_id=session_id,
                parent_node_id="mock_parent",
                answer=user_answer,
                generated_architecture=adapted_arch.architecture,
                candidate_uncertainties=mock_agent_generate_uncertainties()
            )
            
            api_res = answer_journey(answer_req)
            
        blueprint_feasible = False
        blueprint_reqs = 0
        if api_res.status == "BEST_ARCHITECTURE_FOUND":
            blueprint_feasible = True
            blueprint_reqs = len(scenario['requirements'])
            print(f"    BlueprintAI found feasible architecture! Score: {api_res.best_score}")
        elif api_res.status == "NO_FEASIBLE_ARCHITECTURE_FOUND":
            print(f"    BlueprintAI exhausted search, no feasible architecture found.")
            
        results.append({
            "scenario": scenario['name'],
            "base_f": baseline_feasible,
            "blue_f": blueprint_feasible,
            "base_r": baseline_reqs,
            "blue_r": blueprint_reqs
        })
        
    print("\n==================================================")
    print(" FINAL RESULTS                                    ")
    print("==================================================")
    print("Scenario | Base F | Blue F | Base R | Blue R")
    for r in results:
        print(f"{r['scenario'][:15]} | {r['base_f']} | {r['blue_f']} | {r['base_r']} | {r['blue_r']}")

if __name__ == "__main__":
    run_experiment()
