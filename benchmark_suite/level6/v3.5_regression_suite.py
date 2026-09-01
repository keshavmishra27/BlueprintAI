import sys
import os
import subprocess

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

def run_script(script_path: str):
    print(f"\n--- Running {os.path.basename(script_path)} ---")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(f"{script_path} failed with return code {result.returncode}")
    print(result.stdout.strip())
    print("PASS")

def test_optimizer_exclusion():
    from decision_engine.tree.optimizer import optimize_tree
    from decision_engine.tree.tree_schemas import PathNode
    from decision_engine.input_layer.schemas import ArchitectureNode
    
    print("\n--- Testing Optimizer Exclusion ---")
    
    arch = ArchitectureNode(inputs=[], processing=[], decision=[], output=[])
    
    nodes = [
        PathNode(id="node_term", parent_id="root", architecture=arch, status="TERMINAL", path_cost=10.0, path_score=50.0),
        PathNode(id="node_rej", parent_id="root", architecture=arch, status="REJECTED", path_cost=5.0, path_score=100.0, reject_reasons=["some_failure"])
    ]
    
    result = optimize_tree(nodes, {})
    assert result.best_path_id == "node_term", f"Optimizer selected {result.best_path_id}, expected node_term"
    print("PASS: Optimizer excluded REJECTED node despite better score/cost")

def test_normal_architecture_terminal():
    from decision_engine.tree.tree_schemas import PathNode
    from decision_engine.input_layer.schemas import ArchitectureNode, Requirement
    from decision_engine.input_layer.evaluator import evaluate_battle
    from decision_engine.tree.optimizer import evaluate_node_state
    
    print("\n--- Testing Normal Architecture reaches TERMINAL ---")
    
    reqs = []
    constraints = []
    
    arch = ArchitectureNode(
        inputs=["basic data"],
        processing=["basic processing"],
        decision=["basic decision"],
        output=["basic output"],
        capabilities=[],
        semantic_dependencies=[],
        constraints=[]
    )
    
    battle = evaluate_battle(arch, arch, constraints, reqs)
    status = evaluate_node_state(None, is_leaf=True, has_unknowns=False, passes_hard_gates=battle.b_feasible)
    
    assert battle.b_feasible is True, f"Normal architecture should be feasible, got violations: {battle.b_constraint_violations}"
    assert status == "TERMINAL", f"Expected TERMINAL, got {status}"
    assert not battle.b_constraint_violations, f"Expected no reject reasons, got {battle.b_constraint_violations}"
    print("PASS: Normal architecture correctly reaches TERMINAL")

def test_unknown_dependencies_no_reject_reasons():
    from decision_engine.tree.tree_schemas import PathNode
    from decision_engine.input_layer.schemas import ArchitectureNode, Requirement
    from decision_engine.input_layer.evaluator import evaluate_battle
    
    print("\n--- Testing Unknown Dependency does not create reject_reasons ---")
    
    reqs = []
    constraints = []
    
    arch = ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[],
        semantic_dependencies=["requires_unknown_magic_wand"]
    )
    
    battle = evaluate_battle(arch, arch, constraints, reqs)
    
    assert battle.b_feasible is True, "Unknown dependency incorrectly caused infeasibility"
    assert not battle.b_constraint_violations, f"Unknown dependency created reject_reasons: {battle.b_constraint_violations}"
    print("PASS: Unknown dependency remained informational without reject_reasons")

def main():
    base_dir = os.path.dirname(__file__)
    
    test_optimizer_exclusion()
    test_normal_architecture_terminal()
    test_unknown_dependencies_no_reject_reasons()
    
    print("\nAll internal integration tests PASSED.")
    
if __name__ == "__main__":
    main()
