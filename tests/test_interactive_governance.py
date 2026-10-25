import pytest
import itertools
from decision_engine.tree.tree_schemas import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import optimize_tree
from decision_engine.tree.context import DecisionContext
from idea_refiner.parsers.epistemic_resolver import EpistemicResolution
from decision_engine.tree.epistemic import EpistemicValidator

def make_candidate_node(
    node_id: str,
    processing: list,
    dependencies: list,
    cost: float = 10.0,
    score: float = 80.0,
    status: str = "UNRESOLVED"
) -> PathNode:
    arch = ArchitectureNode(
        processing=processing,
        semantic_dependencies=dependencies,
    )
    return PathNode(
        id=node_id,
        parent_id="root",
        architecture=arch,
        status=status,
        path_cost=cost,
        path_score=score,
    )

class TestInteractiveGovernance:
    def test_permutation_invariance_after_resolution(self):
        """
        Prove that regardless of candidate ordering, if an epistemic resolution 
        mutates a candidate's status to feasible, the same mathematically 
        superior candidate always wins.
        """
        # A depends on high_end_hardware, which is missing
        cand_a = make_candidate_node("cand_a", ["Heavy Model"], ["high_end_hardware"], cost=100.0, score=95.0, status="UNRESOLVED")
        
        # B depends on basic_mobile_hardware, which will be provided by resolution
        cand_b = make_candidate_node("cand_b", ["Light Model"], ["basic_mobile_hardware"], cost=10.0, score=85.0, status="UNRESOLVED")
        
        # C requires continuous internet, which is blocked by env constraints
        cand_c = make_candidate_node("cand_c", ["Cloud APIs"], ["requires_continuous_internet"], cost=20.0, score=90.0, status="REJECTED")
        
        context = DecisionContext(
            ontology_version="v1",
            registry_policy_hashes=[],
            environment_constraints=["network: offline"],
            optimizer_preferences={"cost_lambda": 0.5, "epistemic_lambda": 1.0, "complexity_lambda": 0.1, "robustness_lambda": 0.0}
        )
        
        # Simulate EpistemicResolution (Human Answer -> Resolver)
        resolution = EpistemicResolution(
            target="student_hardware",
            normalized_value="low_end",
            provenance="HUMAN_EXPLICIT",
            source_answer="Most students have low-end phones."
        )
        
        results = []
        for perm in itertools.permutations([cand_a, cand_b, cand_c]):
            perm_nodes = [PathNode(**node.model_dump()) for node in perm]
            
            # The Engine validates the resolution and generates branch local states
            updated_graph = []
            for node in perm_nodes:
                is_valid, new_node = EpistemicValidator.validate_and_apply(
                    resolution, node, target_uncertainty="student_hardware"
                )
                if is_valid and new_node:
                    # After branch generation, we assume it's now evaluated to TERMINAL for testing purposes,
                    # if it was not already REJECTED.
                    if new_node.status != "REJECTED":
                        new_node.status = "TERMINAL" if "basic_mobile_hardware" in new_node.architecture.semantic_dependencies else "UNRESOLVED"
                    updated_graph.append(new_node)
                else:
                    updated_graph.append(node)
                    
            res = optimize_tree(updated_graph, context)
            results.append(res)
            
        first_winner = results[0].best_path_id
        assert first_winner == "cand_b_branch_student_hardware_low_end"
        
        # Ensure winner is invariant
        for res in results[1:]:
            assert res.best_path_id == first_winner
            assert res.decision_fingerprint == results[0].decision_fingerprint

    def test_resolver_poisoning_unknown_target(self):
        """
        The Decision Engine must reject an EpistemicResolution with a target not in the ontology.
        """
        resolution = EpistemicResolution(
            target="malicious_hacked_target",
            normalized_value="low_end",
            provenance="HUMAN_EXPLICIT",
            source_answer="I hacked it"
        )
        node = make_candidate_node("test", [], [])
        
        is_valid, branch = EpistemicValidator.validate_and_apply(resolution, node, target_uncertainty="student_hardware")
        
        assert is_valid is False
        assert branch is None

    def test_resolver_poisoning_unknown_value(self):
        """
        The Decision Engine must reject an EpistemicResolution with an invalid value for a valid target.
        """
        resolution = EpistemicResolution(
            target="student_hardware",
            normalized_value="potato_powered",
            provenance="HUMAN_EXPLICIT",
            source_answer="I have a potato"
        )
        node = make_candidate_node("test", [], [])
        
        is_valid, branch = EpistemicValidator.validate_and_apply(resolution, node, target_uncertainty="student_hardware")
        
        assert is_valid is False
        assert branch is None

    def test_resolver_poisoning_wrong_active_uncertainty(self):
        """
        The Decision Engine must reject an EpistemicResolution if it targets something 
        other than the currently active uncertainty.
        """
        resolution = EpistemicResolution(
            target="student_hardware",
            normalized_value="high_end",
            provenance="HUMAN_EXPLICIT",
            source_answer="They are rich"
        )
        node = make_candidate_node("test", [], [])
        
        is_valid, branch = EpistemicValidator.validate_and_apply(resolution, node, target_uncertainty="some_other_uncertainty")
        
        assert is_valid is False
        assert branch is None
