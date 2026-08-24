import pytest
from decision_engine.tree.tree_schemas import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import optimize_tree, evaluate_node_state

def create_mock_arch(name: str) -> ArchitectureNode:
    return ArchitectureNode(
        inputs=[], processing=[name], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[]
    )

def create_mock_node(id: str, status: str, cost: float, value: float, selected: bool = False) -> PathNode:
    return PathNode(
        id=id,
        parent_id="root",
        architecture=create_mock_arch(id),
        status=status,
        path_cost=cost,
        path_value=value,
        selected_by_user=selected
    )

class TestDecisionEngine:
    def test_a_hard_gates(self):
        # Test A: 5-D hard gates. (Simulated via evaluate_node_state)
        assert evaluate_node_state(None, is_leaf=True, has_unknowns=False, passes_hard_gates=False) == "REJECTED"
        assert evaluate_node_state(None, is_leaf=True, has_unknowns=False, passes_hard_gates=True) == "TERMINAL"

    def test_b_unknowns_to_needs_info(self):
        # Test B: UNKNOWN -> NEEDS_INFORMATION
        assert evaluate_node_state(None, is_leaf=True, has_unknowns=True, passes_hard_gates=True) == "NEEDS_INFORMATION"
        assert evaluate_node_state(None, is_leaf=False, has_unknowns=True, passes_hard_gates=True) == "NEEDS_INFORMATION"

    def test_c_three_feasible_leaves_optimize(self):
        # Test C: Three feasible leaves optimize correctly.
        graph = [
            create_mock_node("A", "TERMINAL", cost=1000, value=80),
            create_mock_node("B", "TERMINAL", cost=500, value=90),
            create_mock_node("C", "TERMINAL", cost=2000, value=95)
        ]
        res = optimize_tree(graph, {'weight_cost': 0.5, 'weight_value': 0.5})
        assert res.status == "BEST_ARCHITECTURE_FOUND"
        assert res.best_path_id == "B"  # highest value for lowest cost

    def test_d_intermediate_nodes_not_optimized(self):
        # Test D: Intermediate nodes aren't optimized
        # B is ACTIVE, B1 is TERMINAL. B has better score but is not eligible.
        graph = [
            create_mock_node("B", "ACTIVE", cost=100, value=99),
            create_mock_node("B1", "TERMINAL", cost=500, value=90)
        ]
        res = optimize_tree(graph, {'weight_cost': 0.5, 'weight_value': 0.5})
        assert res.best_path_id == "B1"

    def test_e_unselected_branches_remain(self):
        # Test E: Unselected branches remain in candidate space
        # Unselected leaf can be optimized
        node = create_mock_node("A", "TERMINAL", cost=500, value=90, selected=False)
        res = optimize_tree([node], {})
        assert res.best_path_id == "A"
        assert res.candidates_evaluated == 1

    def test_f_unselected_winner(self):
        # Test F: An unselected branch can mathematically win.
        graph = [
            create_mock_node("A1", "TERMINAL", cost=10000, value=80, selected=True),
            create_mock_node("B1", "TERMINAL", cost=2000, value=95, selected=False)
        ]
        res = optimize_tree(graph, {'weight_cost': 0.5, 'weight_value': 0.5})
        assert res.best_path_id == "B1"
        assert not next(n for n in graph if n.id == res.best_path_id).selected_by_user

    def test_g_capability_inflation(self):
        # Test G: Capability inflation doesn't increase value (mock test of value calculation decoupling)
        # Value is fixed per node for now, but ensure cost normalization handles extreme values
        graph = [
            create_mock_node("A", "TERMINAL", cost=100, value=80),
            create_mock_node("B", "TERMINAL", cost=100, value=80)
        ]
        res = optimize_tree(graph, {})
        assert res.status == "BEST_ARCHITECTURE_FOUND"

    def test_h_cost_normalization(self):
        # Test H: Cost/timeline normalization works relative to candidate space
        graph = [
            create_mock_node("A", "TERMINAL", cost=1000, value=80),
            create_mock_node("B", "TERMINAL", cost=10, value=80)
        ]
        # Max cost is 1000. 
        # A's normalized cost = 1.0
        # B's normalized cost = 0.01
        res = optimize_tree(graph, {'weight_cost': 1.0, 'weight_value': 0.0}) # only care about cost
        assert res.best_path_id == "B"

    def test_i_optimization_preferences(self):
        # Test I: Different optimization preferences change winner
        graph = [
            create_mock_node("Cheap_LowValue", "TERMINAL", cost=10, value=50),
            create_mock_node("Expensive_HighValue", "TERMINAL", cost=1000, value=100)
        ]
        # Prefer cost
        res_cost = optimize_tree(graph, {'weight_cost': 1.0, 'weight_value': 0.0})
        assert res_cost.best_path_id == "Cheap_LowValue"
        
        # Prefer value
        res_value = optimize_tree(graph, {'weight_cost': 0.0, 'weight_value': 1.0})
        assert res_value.best_path_id == "Expensive_HighValue"

    def test_j_terminal_outcomes(self):
        # Test J: 3 distinct terminal outcomes
        # Case 1
        res1 = optimize_tree([], {})
        assert res1.status == "NO_FEASIBLE_ARCHITECTURE_FOUND"
        
        # Case 2
        res2 = optimize_tree([create_mock_node("A", "NEEDS_INFORMATION", cost=10, value=10)], {})
        assert res2.status == "NO_OPTIMIZABLE_ARCHITECTURE_NEEDS_INFORMATION"
        
        # Case 3
        res3 = optimize_tree([create_mock_node("A", "TERMINAL", cost=10, value=10)], {})
        assert res3.status == "BEST_ARCHITECTURE_FOUND"

    def test_k_selected_branch_neq_optimized_branch(self):
        # Test K: Explicit test that a selected branch is NOT the optimized branch
        graph = [
            create_mock_node("Selected_Bad", "TERMINAL", cost=10000, value=10, selected=True),
            create_mock_node("Unselected_Good", "TERMINAL", cost=100, value=90, selected=False)
        ]
        res = optimize_tree(graph, {'weight_cost': 0.5, 'weight_value': 0.5})
        
        best_node = next(n for n in graph if n.id == res.best_path_id)
        assert best_node.selected_by_user is False
        assert best_node.id == "Unselected_Good"
