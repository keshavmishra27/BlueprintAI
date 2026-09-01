import sys
import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement
from decision_engine.input_layer.evaluator import evaluate_battle

def run_evaluation():
    with open(Path(__file__).parent / "baseline_arch.json", "r") as f:
        arch_data = json.load(f)
        
    arch = ArchitectureNode(**arch_data)
    
    constraints = [
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
    
    battle = evaluate_battle(arch, arch, constraints, requirements)
    
    print("=== BASELINE EVALUATION ===")
    print(f"Feasible? {battle.b_feasible}")
    print(f"Violations: {battle.b_constraint_violations}")
    
    reqs_met = sum(1 for r in battle.requirement_evaluations if r.player_b_satisfies)
    print(f"Requirements Met: {reqs_met}/{len(requirements)}")
    
    md = f"""# Run A: Baseline Evaluation

## Architecture
```json
{json.dumps(arch_data, indent=2)}
```

## Python Engine Evaluation
- **Feasible**: {battle.b_feasible}
- **Violations**: {len(battle.b_constraint_violations)} {battle.b_constraint_violations}
- **Requirements Satisfied**: {reqs_met}/{len(requirements)}
"""
    with open(Path(__file__).parent / "plain_antigravity_run.md", "w") as f:
        f.write(md)
        
    print("Evaluation saved to plain_antigravity_run.md")

if __name__ == "__main__":
    run_evaluation()
