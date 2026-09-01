import pytest
from decision_engine.tree.tree_schemas import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import optimize_tree, evaluate_node_state
from decision_engine.tree.context import DecisionContext

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

def create_mock_context(prefs: dict = None) -> DecisionContext:
    if prefs is None:
        prefs = {}
    return DecisionContext(
        ontology_version="v1",
        registry_policy_hashes=[],
        environment_constraints=[],
        optimizer_preferences=prefs
    )

class TestDecisionEngine:
    def test_a_hard_gates(self):
        assert evaluate_node_state(None, is_leaf=True, has_unknowns=False, passes_hard_gates=False) == "REJECTED"
        assert evaluate_node_state(None, is_leaf=True, has_unknowns=False, passes_hard_gates=True) == "TERMINAL"

    def test_b_unknowns_to_needs_info(self):
        assert evaluate_node_state(None, is_leaf=True, has_unknowns=True, passes_hard_gates=True) == "UNRESOLVED"
        assert evaluate_node_state(None, is_leaf=False, has_unknowns=True, passes_hard_gates=True) == "UNRESOLVED"

    def test_c_three_feasible_leaves_optimize(self):
        graph = [
            create_mock_node("A", "TERMINAL", cost=1000, value=80),
            create_mock_node("B", "TERMINAL", cost=500, value=90),
            create_mock_node("C", "TERMINAL", cost=2000, value=95)
        ]
        res = optimize_tree(graph, create_mock_context({'cost_lambda': 0.5, 'robustness_lambda': 0.0}))
        assert res.status == "TERMINAL"
        assert res.best_path_id == "B"

    def test_d_intermediate_nodes_not_optimized(self):
        graph = [
            create_mock_node("B", "ACTIVE", cost=100, value=99),
            create_mock_node("B1", "TERMINAL", cost=500, value=90)
        ]
        res = optimize_tree(graph, create_mock_context({'cost_lambda': 0.5}))
        assert res.best_path_id == "B1"

    def test_e_unselected_branches_remain(self):
        node = create_mock_node("A", "TERMINAL", cost=500, value=90, selected=False)
        res = optimize_tree([node], create_mock_context({}))
        assert res.best_path_id == "A"
        assert res.candidates_evaluated == 1

    def test_f_unselected_winner(self):
        graph = [
            create_mock_node("A1", "TERMINAL", cost=10000, value=80, selected=True),
            create_mock_node("B1", "TERMINAL", cost=2000, value=95, selected=False)
        ]
        res = optimize_tree(graph, create_mock_context({'cost_lambda': 0.5}))
        assert res.best_path_id == "B1"
        assert not next(n for n in graph if n.id == res.best_path_id).selected_by_user

    def test_g_capability_inflation(self):
        graph = [
            create_mock_node("A", "TERMINAL", cost=100, value=80),
            create_mock_node("B", "TERMINAL", cost=100, value=80)
        ]
        res = optimize_tree(graph, create_mock_context({}))
        assert res.status == "TERMINAL"

    def test_h_cost_normalization(self):
        graph = [
            create_mock_node("A", "TERMINAL", cost=1000, value=80),
            create_mock_node("B", "TERMINAL", cost=10, value=80)
        ]
        res = optimize_tree(graph, create_mock_context({'cost_lambda': 1.0}))
        assert res.best_path_id == "B"

    def test_i_optimization_preferences(self):
        graph = [
            create_mock_node("Cheap_LowValue", "TERMINAL", cost=10, value=50),
            create_mock_node("Expensive_HighValue", "TERMINAL", cost=1000, value=100)
        ]
        res_cost = optimize_tree(graph, create_mock_context({'cost_lambda': 1.0, 'epistemic_lambda': 0.0}))
        assert res_cost.best_path_id == "Cheap_LowValue"
        
        res_value = optimize_tree(graph, create_mock_context({'cost_lambda': -0.1, 'epistemic_lambda': 0.0}))
        assert res_value.best_path_id == "Expensive_HighValue"

    def test_j_terminal_outcomes(self):
        res1 = optimize_tree([], create_mock_context({}))
        assert res1.status == "NO_FEASIBLE_ARCHITECTURE_FOUND"
        
        res2 = optimize_tree([create_mock_node("A", "NEEDS_INFORMATION", cost=10, value=10)], create_mock_context({}))
        assert res2.status == "CONTINUE"
        
        res3 = optimize_tree([create_mock_node("A", "TERMINAL", cost=10, value=10)], create_mock_context({}))
        assert res3.status == "TERMINAL"

    def test_k_selected_branch_neq_optimized_branch(self):
        graph = [
            create_mock_node("Selected_Bad", "TERMINAL", cost=10000, value=10, selected=True),
            create_mock_node("Unselected_Good", "TERMINAL", cost=100, value=90, selected=False)
        ]
        res = optimize_tree(graph, create_mock_context({'cost_lambda': 0.5}))
        
        best_node = next(n for n in graph if n.id == res.best_path_id)
        assert best_node.selected_by_user is False
        assert best_node.id == "Unselected_Good"
