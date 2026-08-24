import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from decision_engine.tree import benchmark_evaluator
from benchmark_suite.runner import run_benchmark_scenario

def test_sentinel_sensitivity():
    scenario_path = Path(__file__).parent / "scenarios" / "test_hidden_assumption.json"
    
    sentinels = [-10.0, -100.0, -1000.0, -10000.0]
    
    for s in sentinels:
        print(f"\n=======================================================")
        print(f"RUNNING SENTINEL SENSITIVITY TEST: INFEASIBLE_SENTINEL = {s}")
        print(f"=======================================================")
        benchmark_evaluator.INFEASIBLE_SENTINEL = s
        benchmark_evaluator.globals = lambda: {"INFEASIBLE_SENTINEL": s}
        # Actually globals() in compute_s_abs pulls from the module's globals.
        # We can just update it in the module directly.
        setattr(benchmark_evaluator, "INFEASIBLE_SENTINEL", s)
        # Python globals() inside benchmark_evaluator will naturally see this update.
        
        run_benchmark_scenario(scenario_path)

if __name__ == "__main__":
    test_sentinel_sensitivity()
