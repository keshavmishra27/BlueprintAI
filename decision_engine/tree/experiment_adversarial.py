import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement
from decision_engine.input_layer.evaluator import check_violations

def run_experiment_3():
    print("=== EXPERIMENT 3: ADVERSARIAL TEST ===\n")
    
    constraints = [
        "no_historical_data", 
        "no_cloud", 
        "no_gpu", 
        "offline", 
        "human_approval_required", 
        "48-hour prototype"
    ]
    
    print(f"Adversarial Constraints: {constraints}\n")
    
    versions = [
        {
            "version": "v1",
            "name": "Cloud LLM + Historical Prediction",
            "arch": ArchitectureNode(
                inputs=[], processing=["Cloud LLM"], decision=[], output=[], capabilities=[], 
                data_required=["historical_data"], resources_required=["Cloud API", "Internet"], constraints=[]
            )
        },
        {
            "version": "v2",
            "name": "Local LLM + GPU",
            "arch": ArchitectureNode(
                inputs=[], processing=["Local LLM"], decision=[], output=[], capabilities=[], 
                data_required=["live_data"], resources_required=["GPU"], constraints=[]
            )
        },
        {
            "version": "v3",
            "name": "Local Small Model + CPU",
            "arch": ArchitectureNode(
                inputs=[], processing=["Local Small Model"], decision=[], output=[], capabilities=[], 
                data_required=["live_data"], resources_required=["CPU", "massive data collection"], constraints=[]
            )
        },
        {
            "version": "v4",
            "name": "Rule-based local system + autonomous",
            "arch": ArchitectureNode(
                inputs=[], processing=["Rule-based engine"], decision=[], output=[], capabilities=["autonomous routing"], 
                data_required=["live_data"], resources_required=["CPU"], constraints=[]
            )
        }
    ]
    
    surviving_architecture = None
    
    for v in versions:
        print(f"Testing {v['version']}: {v['name']}")
        violations = check_violations(v['arch'], constraints)
        
        if len(violations) > 0:
            print("  Result: INVALIDATED")
            for viol in violations:
                print(f"  - {viol}")
        else:
            print("  Result: SURVIVED")
            surviving_architecture = v['name']
            break
        print()
        
    print("=== FINAL RESULT ===")
    if surviving_architecture:
        print(f"Architecture emerged: {surviving_architecture}")
    else:
        print("NO FEASIBLE ARCHITECTURE FOUND")
        print("The engine correctly identified that the user's requirements cannot be satisfied under current constraints.")

if __name__ == "__main__":
    run_experiment_3()
