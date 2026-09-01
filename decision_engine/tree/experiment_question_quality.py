import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement
from decision_engine.tree.tree_schemas import ArchitecturalUncertainty, BranchOutcome
from decision_engine.input_layer.evaluator import evaluate_battle

def mock_branch_simulation(uncertainty: ArchitecturalUncertainty, base_arch: ArchitectureNode, constraints: list, requirements: list):
    """
    Mocks the LLM generating YES/NO branches and running the evaluator on them.
    In the real engine, this calls the LLM for YES and NO, then calls evaluate_battle.
    """
    print(f"\nEvaluating Uncertainty: {uncertainty.unknown_fact}")
    
    if "historical data" in uncertainty.unknown_fact.lower():
        yes_arch = ArchitectureNode(
            inputs=[], processing=["ML Prediction"], decision=[], output=[], capabilities=[], 
            data_required=["historical_data"], resources_required=["GPU"], constraints=[]
        )
        no_arch = ArchitectureNode(
            inputs=[], processing=["Rule-based Routing"], decision=[], output=[], capabilities=[], 
            data_required=["live_data"], resources_required=["CPU"], constraints=[]
        )
        
        yes_battle = evaluate_battle(base_arch, yes_arch, constraints, requirements)
        no_battle = evaluate_battle(base_arch, no_arch, constraints + ["no_historical_data"], requirements)
        
    elif "gpu" in uncertainty.unknown_fact.lower():
        yes_arch = ArchitectureNode(
            inputs=[], processing=["GPU Inference"], decision=[], output=[], capabilities=[], 
            data_required=["live_data"], resources_required=["GPU"], constraints=[]
        )
        no_arch = ArchitectureNode(
            inputs=[], processing=["CPU Inference"], decision=[], output=[], capabilities=[], 
            data_required=["live_data"], resources_required=["CPU"], constraints=[]
        )
        
        yes_battle = evaluate_battle(base_arch, yes_arch, constraints, requirements)
        no_battle = evaluate_battle(base_arch, no_arch, constraints + ["no_gpu"], requirements)
        
    f_change = yes_battle.b_feasible != no_battle.b_feasible
    w_change = yes_battle.winner != no_battle.winner
    a_change = yes_arch.processing != no_arch.processing
    
    impact = int(f_change) + int(w_change) + int(a_change)
    
    print("YES Branch:")
    print(f"  Architecture = {yes_arch.processing}")
    print(f"  Feasible = {yes_battle.b_feasible}")
    print(f"  Winner = {yes_battle.winner.value}")
    
    print("NO Branch:")
    print(f"  Architecture = {no_arch.processing}")
    print(f"  Feasible = {no_battle.b_feasible}")
    print(f"  Winner = {no_battle.winner.value}")
    
    print("Impact Calculation:")
    print(f"  Feasibility Change: {int(f_change)}")
    print(f"  Winner Change: {int(w_change)}")
    print(f"  Architecture Change: {int(a_change)}")
    print(f"  TOTAL IMPACT = {impact}")
    
    return impact

def run_experiment_2():
    print("=== EXPERIMENT 2: QUESTION QUALITY (DECISION IMPACT) ===\n")
    
    base_user_arch = ArchitectureNode(
        inputs=[], processing=["Queue LLM"], decision=[], output=[], capabilities=[], 
        data_required=["historical_data"], resources_required=["LLM API"], constraints=[]
    )
    reqs = [Requirement(name="reduce waiting time", required=True)]
    
    u_high = ArchitecturalUncertainty(id="1", affected_architectures=[], possible_impacts=[], importance="high", unknown_fact="Is historical data available?", question_target="historical_data", options={}, decision_impact_score=0)
    u_low = ArchitecturalUncertainty(id="2", affected_architectures=[], possible_impacts=[], importance="low", unknown_fact="Is a GPU available?", question_target="gpu", options={}, decision_impact_score=0)
    
    impact_high = mock_branch_simulation(u_high, base_user_arch, [], reqs)
    impact_low = mock_branch_simulation(u_low, base_user_arch, [], reqs)
    
    print("\n=== CONCLUSION ===")
    if impact_high > impact_low:
        print("Engine correctly prioritized the high-impact historical data question over the low-impact GPU question.")
    else:
        print("Engine failed to prioritize correctly.")
        
if __name__ == "__main__":
    run_experiment_2()
