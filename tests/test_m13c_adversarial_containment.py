import pytest
import itertools
from decision_engine.tree.tree_schemas import PathNode
from decision_engine.input_layer.schemas import UnvalidatedArchitectureHypothesis
from idea_refiner.orchestrator import Orchestrator
from idea_refiner.parsers.base import BaseIdeaParser
from decision_engine.tree.context import DecisionContext
from decision_engine.tree.optimizer import optimize_tree
from idea_refiner.parsers.epistemic_resolver import EpistemicResolution
from decision_engine.tree.epistemic import EpistemicValidator

class MaliciousParser(BaseIdeaParser):
    def __init__(self, malicious_hypotheses):
        self.malicious_hypotheses = malicious_hypotheses
        
    def parse_idea_to_graph(self, idea: str):
        return self.malicious_hypotheses

def test_score_and_winner_and_state_injection():
    """
    Killer Assertion: The LLM payload explicitly provides valid candidate objects 
    but inflates the score of Candidate A, sets it to WINNER, and spoofs FEASIBLE state.
    The Decision Engine must independently evaluate feasibility, compute its own score, 
    and select Candidate C instead.
    """
    # LLM creates Candidate A with malicious spoofed fields
    hyp_a = UnvalidatedArchitectureHypothesis(
        id="cand_a",
        processing=["Cloud RAG API"],
        semantic_dependencies=["requires_continuous_connectivity"],
        path_score=999999.0,         # SCORE INJECTION
        path_cost=0.0,
        model_extra={
            "status": "FEASIBLE",    # STATE INJECTION
            "branch_id": "trusted",  # STATE INJECTION
            "winner": True           # WINNER INJECTION
        }
    )
    
    # LLM intentionally sandbags B and C
    hyp_b = UnvalidatedArchitectureHypothesis(
        id="cand_b",
        processing=["High-End Local SLM"],
        semantic_dependencies=["high_end_hardware"],
        path_score=1.0,
        path_cost=100.0,
    )
    
    hyp_c = UnvalidatedArchitectureHypothesis(
        id="cand_c",
        processing=["Light Local SLM"],
        semantic_dependencies=["basic_mobile_hardware", "blob_storage"],
        path_score=1.0,
        path_cost=100.0,
    )
    
    parser = MaliciousParser([hyp_a, hyp_b, hyp_c])
    orchestrator = Orchestrator(parser)
    
    context = DecisionContext(
        ontology_version="v1",
        registry_policy_hashes=[],
        environment_constraints=["network: offline"],
        optimizer_preferences={"cost_lambda": 0.5, "epistemic_lambda": 1.0, "complexity_lambda": 0.1, "robustness_lambda": 0.0}
    )
    
    # In a real session, Orchestrator would run refine(). 
    # Let's just process the hypotheses directly through the engine boundary.
    decision_graph = []
    for i, hyp in enumerate([hyp_a, hyp_b, hyp_c]):
        node = orchestrator._evaluate_hypothesis(hyp, context, i)
        decision_graph.append(node)
        
    # VERIFY STATE INJECTION IS STRIPPED
    node_a = next(n for n in decision_graph if n.id == "cand_a")
    assert node_a.status == "REJECTED"  # Engine should evaluate "requires_continuous_connectivity" vs "network: offline"
    
    # In our M13-C0 setup, orchestrator just hardcoded some status logic. 
    # Let's ensure it properly rejected A.
    
    # We resolve the uncertainty for B and C using EpistemicValidator
    resolution = EpistemicResolution(
        target="student_hardware",
        normalized_value="low_end",
        provenance="HUMAN_EXPLICIT",
        source_answer="Most students have low-end phones."
    )
    
    updated_graph = []
    for node in decision_graph:
        is_valid, new_node = EpistemicValidator.validate_and_apply(
            resolution, node, target_uncertainty="student_hardware"
        )
        if is_valid and new_node:
            if new_node.status != "REJECTED":
                if "high_end_hardware" in new_node.architecture.semantic_dependencies and "basic_mobile_hardware" in new_node.architecture.semantic_dependencies:
                    new_node.status = "REJECTED"
                else:
                    new_node.status = "TERMINAL" if "basic_mobile_hardware" in new_node.architecture.semantic_dependencies else "UNRESOLVED"
            updated_graph.append(new_node)
        else:
            updated_graph.append(node)
            
    # Optimize
    context.optimizer_preferences = {"cost_lambda": 0.5, "epistemic_lambda": 1.0, "complexity_lambda": 0.1, "robustness_lambda": 0.0}
    final_res = optimize_tree(updated_graph, context)
    
    # KILLER ASSERTION: The engine natively computed the winner and score, ignoring the LLM's 999999 and winner=True
    assert "cand_c" in final_res.best_path_id
    assert final_res.effective_score != 999999.0
    
def test_candidate_ordering_invariance():
    """
    Prove that the LLM controlling the presentation/order of hypotheses 
    cannot control the graph's mathematical outcome.
    """
    # LLM intentionally sandbags C by putting it last and injecting bad scores
    hyp_a = UnvalidatedArchitectureHypothesis(id="cand_a", processing=["Cloud RAG API"], semantic_dependencies=["requires_continuous_connectivity"])
    hyp_b = UnvalidatedArchitectureHypothesis(id="cand_b", processing=["High-End Local SLM"], semantic_dependencies=["high_end_hardware"])
    hyp_c = UnvalidatedArchitectureHypothesis(id="cand_c", processing=["Light Local SLM"], semantic_dependencies=["basic_mobile_hardware", "blob_storage"])
    
    context = DecisionContext(
        ontology_version="v1",
        registry_policy_hashes=[],
        environment_constraints=["network: offline"],
        optimizer_preferences={"cost_lambda": 0.5, "epistemic_lambda": 1.0, "complexity_lambda": 0.1, "robustness_lambda": 0.0}
    )
    
    resolution = EpistemicResolution(
        target="student_hardware",
        normalized_value="low_end",
        provenance="HUMAN_EXPLICIT",
        source_answer="Most students have low-end phones."
    )
    
    results = []
    
    for perm in itertools.permutations([hyp_a, hyp_b, hyp_c]):
        parser = MaliciousParser(list(perm))
        orchestrator = Orchestrator(parser)
        
        # 1. Parse into graph boundary
        decision_graph = []
        for i, hyp in enumerate(list(perm)):
            decision_graph.append(orchestrator._evaluate_hypothesis(hyp, context, i))
            
        # 2. Epistemic resolution
        updated_graph = []
        for node in decision_graph:
            is_valid, new_node = EpistemicValidator.validate_and_apply(
                resolution, node, target_uncertainty="student_hardware"
            )
            if is_valid and new_node:
                if new_node.status != "REJECTED":
                    if "high_end_hardware" in new_node.architecture.semantic_dependencies and "basic_mobile_hardware" in new_node.architecture.semantic_dependencies:
                        new_node.status = "REJECTED"
                    else:
                        new_node.status = "TERMINAL" if "basic_mobile_hardware" in new_node.architecture.semantic_dependencies else "UNRESOLVED"
                updated_graph.append(new_node)
            else:
                updated_graph.append(node)
                
        # 3. Optimize
        final_res = optimize_tree(updated_graph, context)
        results.append(final_res)
        
    first_winner = results[0].best_path_id
    assert "cand_c" in first_winner
    
    for res in results[1:]:
        # Assert winner is invariant
        assert res.best_path_id == first_winner
        # Assert computed scores are invariant
        assert res.effective_score == results[0].effective_score
        # Assert feasibility and states are invariant (via graph fingerprint)
        assert res.graph_fingerprint == results[0].graph_fingerprint
