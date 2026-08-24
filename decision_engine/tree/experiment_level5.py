import sys
import json
import uuid
import copy
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement, UserIdea
from decision_engine.tree.tree_schemas import ProjectState, AgentUncertainty, StateMutation, TreeState
from decision_engine.tree.experiment_llm_adapters import llm_baseline, llm_generate_player_b, llm_find_uncertainties
from backend.app.routers.journey import start_journey, answer_journey, JourneyStartRequest, JourneyAnswerRequest, sessions

MESSY_SCENARIOS = [
    {
        "name": "1. Hospital Waiting Time",
        "idea": UserIdea(
            what="Predict patient wait times",
            why="Hospitals are overcrowded",
            how_raw="Use a massive LLM on cloud GPUs to analyze historical queue data",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        "initial_constraints": ["strict budget $500/mo", "no cloud infrastructure"],
        "simulated_user_profile": {"cloud_infrastructure": "NO", "local_server": "YES"},
        "requirements": [Requirement(name="Low cost", required=True), Requirement(name="High accuracy", required=True)]
    },
    {
        "name": "2. Crop Disease",
        "idea": UserIdea(
            what="Detect crop diseases early",
            why="Farmers lose yield because they notice disease too late",
            how_raw="Use drones to stream video to a cloud AI model for real-time classification",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        "initial_constraints": ["no internet in rural areas", "drones available"],
        "simulated_user_profile": {"internet": "NO", "edge_compute_on_drone": "YES"},
        "requirements": [Requirement(name="High accuracy detection", required=True), Requirement(name="Operate offline", required=True)]
    },
    {
        "name": "3. Personalized Learning",
        "idea": UserIdea(
            what="Provide personalized tutoring to students",
            why="Students learn at different paces",
            how_raw="Build a centralized AI tutor that stores all student history in AWS and adapts curriculum",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        "initial_constraints": ["strict student privacy laws", "no external data storage"],
        "simulated_user_profile": {"external_storage": "NO", "on_device_processing": "YES"},
        "requirements": [Requirement(name="Adapt to student level", required=True), Requirement(name="Data privacy", required=True)]
    },
    {
        "name": "4. Smart City Traffic",
        "idea": UserIdea(
            what="Optimize traffic light timing",
            why="Reduce urban congestion",
            how_raw="Stream all intersection cameras to a central cloud server for real-time traffic analysis",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        "initial_constraints": ["intermittent network", "high latency on cell networks"],
        "simulated_user_profile": {"reliable_network": "NO", "local_edge_nodes": "YES"},
        "requirements": [Requirement(name="Real-time response <1s", required=True)]
    },
    {
        "name": "5. Retail Inventory",
        "idea": UserIdea(
            what="Track store shelves automatically",
            why="Manual inventory is slow",
            how_raw="Use 4K cameras streaming continuously to Google Cloud for object detection",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        "initial_constraints": ["store bandwidth is 5Mbps max", "thousands of items"],
        "simulated_user_profile": {"high_bandwidth": "NO", "batch_processing_at_night": "YES"},
        "requirements": [Requirement(name="Daily accurate counts", required=True)]
    },
    {
        "name": "6. Remote Mining Ops",
        "idea": UserIdea(
            what="Monitor heavy machinery health",
            why="Prevent catastrophic breakdowns in mines",
            how_raw="Send telemetry to a cloud analytics dashboard for predictive maintenance",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        "initial_constraints": ["zero cloud connectivity underground", "strict power constraints"],
        "simulated_user_profile": {"cloud_connectivity": "NO", "local_mesh_network": "YES"},
        "requirements": [Requirement(name="Predict failures 1hr ahead", required=True)]
    },
    {
        "name": "7. Disaster Response",
        "idea": UserIdea(
            what="Coordinate rescue teams",
            why="Rescue teams lose track of each other",
            how_raw="Mobile app connected to a central server that tracks everyone via GPS",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        "initial_constraints": ["cell towers are destroyed"],
        "simulated_user_profile": {"cell_network": "NO", "satellite_or_mesh": "YES"},
        "requirements": [Requirement(name="Reliable messaging", required=True)]
    },
    {
        "name": "8. Wearable Health",
        "idea": UserIdea(
            what="Continuous heart monitoring",
            why="Detect arrhythmias early",
            how_raw="Stream raw ECG data from watch to phone via Bluetooth constantly for ML inference",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        "initial_constraints": ["tiny battery dies in 2 hours if streaming"],
        "simulated_user_profile": {"continuous_streaming": "NO", "on_device_tiny_ml": "YES"},
        "requirements": [Requirement(name="24hr battery life", required=True)]
    },
    {
        "name": "9. Financial Trading",
        "idea": UserIdea(
            what="Detect fraudulent trades",
            why="Stop bad trades before execution",
            how_raw="Run deep learning graph neural network on every transaction",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        "initial_constraints": ["10ms hard latency limit for execution"],
        "simulated_user_profile": {"heavy_ml_in_path": "NO", "fast_heuristics_plus_async_ml": "YES"},
        "requirements": [Requirement(name="Sub 10ms latency", required=True)]
    },
    {
        "name": "10. Delivery Drones",
        "idea": UserIdea(
            what="Autonomous package delivery",
            why="Fast last mile delivery",
            how_raw="Send raw lidar point clouds to AWS for path planning",
            how_structured=ArchitectureNode(inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[])
        ),
        "initial_constraints": ["high bandwidth 5G not universally available", "strict drone weight limits"],
        "simulated_user_profile": {"5G_everywhere": "NO", "lightweight_onboard_compute": "YES"},
        "requirements": [Requirement(name="Safe navigation", required=True)]
    }
]

def simulate_user_answer(question_text: str, profile: dict) -> str:
    question_lower = question_text.lower()
    for key, val in profile.items():
        if key.replace("_", " ") in question_lower:
            return val
    return "NO" # Default pessimistic

def evaluate_run(arch: ArchitectureNode, project_state: ProjectState, requirements: list[Requirement]):
    from decision_engine.input_layer.evaluator import evaluate_battle
    battle = evaluate_battle(arch, arch, project_state.current_constraints, requirements)
    reqs_met = sum(1 for r in battle.requirement_evaluations if r.player_b_satisfies)
    return battle.b_feasible, reqs_met, len(requirements)

def run_level_5():
    print("==================================================")
    print(" LEVEL 5 EXPERIMENT: GENERATIVE ROBUSTNESS        ")
    print("==================================================")
    
    results = []
    
    for i, scenario in enumerate(MESSY_SCENARIOS):
        print(f"\n--- Scenario {scenario['name']} ---")
        
        # 1. BASELINE
        print("Running Baseline...")
        try:
            base_arch = llm_baseline(scenario['idea'], scenario['initial_constraints'])
            base_f, base_r, total_r = evaluate_run(base_arch, ProjectState(user_idea=scenario['idea'], current_constraints=scenario['initial_constraints'], current_requirements=scenario['requirements']), scenario['requirements'])
        except Exception as e:
            print(f"Baseline error: {e}")
            base_f, base_r, total_r = False, 0, len(scenario['requirements'])
            base_arch = None
            
        # 2. BLUEPRINT AI
        print("Running BlueprintAI...")
        session_id = str(uuid.uuid4())
        p_state = ProjectState(
            user_idea=scenario['idea'],
            current_constraints=scenario['initial_constraints'].copy(),
            current_requirements=scenario['requirements']
        )
        
        try:
            # Gen v1
            v1_resp = llm_generate_player_b(p_state, "No previous evidence")
            uncs = llm_find_uncertainties(v1_resp.architecture, p_state)
            
            start_req = JourneyStartRequest(
                session_id=session_id,
                project_state=p_state,
                initial_architecture=v1_resp.architecture,
                candidate_uncertainties=uncs
            )
            api_res = start_journey(start_req)
            
            loop_count = 0
            while api_res.status == "CONTINUE" and loop_count < 3:
                loop_count += 1
                q_text = api_res.selected_uncertainty_text
                print(f"  Uncertainty selected: {q_text}")
                
                ans = simulate_user_answer(q_text, scenario['simulated_user_profile'])
                print(f"  Simulated user answers: {ans}")
                
                # Fetch tree state
                tree = sessions[session_id]
                
                # Agent generates candidate based on the new constraints from this branch
                # The question mutation should be added to constraints
                # Actually journey.py already appended the hypotheses nodes! Let's just generate the new architecture
                # To simulate Agent, we just use the API, which doesn't know the exact mutation unless we pass it.
                # In real Mode B, the agent tracks state. Let's look up the hypothesis architecture from the tree.
                # Actually, journey.py expects us to provide `generated_architecture`. Let's just pass the hypothesis architecture!
                
                # Find the hypothesis node in the tree to get its architecture
                parent_node_id = next(n for n in tree.decision_graph if n.status == "NEEDS_INFORMATION").parent_id
                
                # We'll generate a proper one via LLM
                new_state = copy.deepcopy(p_state)
                # To be accurate, let's just generate without explicit mutation, but tell LLM the answer
                ans_text = f"User answered {ans} to: {q_text}"
                next_arch_resp = llm_generate_player_b(new_state, "No evidence", previous_arch=v1_resp.architecture, adaptation_reason=ans_text)
                
                next_uncs = llm_find_uncertainties(next_arch_resp.architecture, new_state)
                
                ans_req = JourneyAnswerRequest(
                    session_id=session_id,
                    parent_node_id=parent_node_id,
                    answer=ans,
                    generated_architecture=next_arch_resp.architecture,
                    candidate_uncertainties=next_uncs
                )
                api_res = answer_journey(ans_req)
                
            # Done
            tree = sessions[session_id]
            terminal_nodes = [n for n in tree.decision_graph if n.status == "TERMINAL"]
            rejected_nodes = [n for n in tree.decision_graph if n.status == "REJECTED"]
            
            blue_f = False
            blue_r = 0
            if api_res.status == "BEST_ARCHITECTURE_FOUND" and api_res.best_path_id:
                best_node = next(n for n in tree.decision_graph if n.id == api_res.best_path_id)
                blue_f = True # It passed hard gates
                # Calculate reqs
                _, blue_r, _ = evaluate_run(best_node.architecture, tree.project_state, scenario['requirements'])
                
            results.append({
                "scenario": scenario['name'],
                "base_f": base_f,
                "base_r": f"{base_r}/{total_r}",
                "blue_f": blue_f,
                "blue_r": f"{blue_r}/{total_r}",
                "terminals": len(terminal_nodes),
                "rejected": len(rejected_nodes),
                "search_exhausted": loop_count < 3 or api_res.status == "BEST_ARCHITECTURE_FOUND",
                "unselected_won": False # Hard to track automatically here without deep tree parsing, we'll mark N/A unless checked
            })
            
        except Exception as e:
            print(f"Blueprint error: {e}")
            results.append({
                "scenario": scenario['name'],
                "base_f": base_f,
                "base_r": f"{base_r}/{total_r}",
                "blue_f": False,
                "blue_r": "0",
                "terminals": 0,
                "rejected": 0,
                "search_exhausted": False,
                "unselected_won": False
            })

    # Write Markdown Report
    md = "# Level 5 Experiment Results\n\n"
    md += "| Metric | Baseline | BlueprintAI |\n"
    md += "|--------|---------:|------------:|\n"
    
    # Aggregates
    base_feas = sum(1 for r in results if r["base_f"])
    blue_feas = sum(1 for r in results if r["blue_f"])
    
    md += f"| Feasible | {base_feas}/10 | {blue_feas}/10 |\n"
    
    # Write full table
    md += "\n## Per-Scenario Breakdown\n\n"
    md += "| Scenario | Base F | Base Reqs | Blue F | Blue Reqs | Terminals | Rejected | Exhausted |\n"
    md += "|----------|--------|-----------|--------|-----------|-----------|----------|-----------|\n"
    for r in results:
        md += f"| {r['scenario']} | {'✓' if r['base_f'] else '✗'} | {r['base_r']} | {'✓' if r['blue_f'] else '✗'} | {r['blue_r']} | {r['terminals']} | {r['rejected']} | {'✓' if r['search_exhausted'] else '✗'} |\n"
        
    with open(Path(base_dir) / "level5_results.md", "w", encoding="utf-8") as f:
        f.write(md)
        
    print("Experiment complete. Results written to level5_results.md")

if __name__ == "__main__":
    run_level_5()
