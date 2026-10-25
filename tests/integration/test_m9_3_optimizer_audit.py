import pytest
from decision_engine.tree.tree_schemas import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import optimize_tree
from decision_engine.tree.context import DecisionContext

def create_mock_arch(name: str) -> ArchitectureNode:
    return ArchitectureNode(
        inputs=[], processing=[name], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[]
    )

def create_mock_node(id: str, status: str, cost: float, value: float, score: float = None) -> PathNode:
    return PathNode(
        id=id,
        parent_id="root",
        architecture=create_mock_arch(id),
        status=status,
        path_cost=cost,
        path_value=value,
        path_score=score if score is not None else value - cost,
        selected_by_user=False
    )

def get_context() -> DecisionContext:
    return DecisionContext(
        ontology_version="v1",
        registry_policy_hashes=[],
        environment_constraints=[],
        optimizer_preferences={}
    )

class TestOptimizerM93Audit:
    """
    Forensic read-only audit to prove the optimizer obeys epistemic status over numerical score.
    The M9.3 invariant: Numerical score NEVER overrides epistemic state.
    """
    
    def test_1_adversarial_needs_information(self):
        """
        Test 1: NEEDS_INFORMATION (9999) vs TERMINAL (10)
        Proves that an unresolved epistemic gap forces the tree to CONTINUE rather than
        mistakenly selecting a high-scoring but unproven architecture.
        """
        candidate_a = create_mock_node("A", "NEEDS_INFORMATION", cost=1, value=10000, score=9999.0)
        candidate_b = create_mock_node("B", "TERMINAL", cost=10, value=20, score=10.0)
        
        graph = [candidate_a, candidate_b]
        res = optimize_tree(graph, get_context())
        
        assert res.status == "CONTINUE"
        assert res.best_path_id is None

    def test_2a_adversarial_invalid_candidate_with_terminal(self):
        """
        Test 2a: INVALID_CANDIDATE (9999) vs TERMINAL (10)
        Proves that INVALID_CANDIDATE is stripped from candidate evaluation completely.
        The lower scoring TERMINAL candidate must win.
        """
        candidate_a = create_mock_node("A", "INVALID_CANDIDATE", cost=1, value=10000, score=9999.0)
        candidate_b = create_mock_node("B", "TERMINAL", cost=10, value=20, score=10.0)
        
        graph = [candidate_a, candidate_b]
        res = optimize_tree(graph, get_context())
        
        assert res.status == "TERMINAL"
        assert res.best_path_id == "B"
        
    def test_2b_solo_invalid_candidate(self):
        """
        Test 2b: INVALID_CANDIDATE (9999) on its own
        Proves that an invalid candidate cannot be selected even if it's the only node
        in the graph.
        """
        candidate_a = create_mock_node("A", "INVALID_CANDIDATE", cost=1, value=10000, score=9999.0)
        
        graph = [candidate_a]
        res = optimize_tree(graph, get_context())
        
        assert res.status == "NO_FEASIBLE_ARCHITECTURE_FOUND"
        assert res.best_path_id is None

    def test_3_adversarial_unexplored_hypothesis(self):
        """
        Test 3: UNEXPLORED_HYPOTHESIS (9999) vs TERMINAL (10)
        Proves that an unexplored question branch forces a CONTINUE.
        """
        candidate_a = create_mock_node("A", "UNEXPLORED_HYPOTHESIS", cost=1, value=10000, score=9999.0)
        candidate_b = create_mock_node("B", "TERMINAL", cost=10, value=20, score=10.0)
        
        graph = [candidate_a, candidate_b]
        res = optimize_tree(graph, get_context())
        
        assert res.status == "CONTINUE"
        assert res.best_path_id is None

    def test_4_strict_terminal_evaluation(self):
        """
        Test 4: UNRESOLVED (90) vs TERMINAL (100)
        Proves that when candidates are legally in the candidate space, the optimizer
        can accurately evaluate and rank them based on score/preferences.
        """
        candidate_a = create_mock_node("A", "UNRESOLVED", cost=10, value=100, score=90.0)
        candidate_b = create_mock_node("B", "TERMINAL", cost=10, value=110, score=100.0)
        
        graph = [candidate_a, candidate_b]
        
        res = optimize_tree(graph, get_context())
        
        assert res.status in ["TERMINAL", "UNRESOLVED"]
        assert res.best_path_id == "B"
