import pytest
from decision_engine.input_layer.schemas import UnvalidatedArchitectureHypothesis
from idea_refiner.orchestrator import Orchestrator
from idea_refiner.parsers.base import BaseIdeaParser
from decision_engine.tree.context import DecisionContext
from decision_engine.tree.optimizer import optimize_tree
from idea_refiner.parsers.epistemic_resolver import EpistemicResolution
from decision_engine.tree.epistemic import EpistemicValidator

class MockParser(BaseIdeaParser):
    def __init__(self, hypotheses):
        self.hypotheses = hypotheses
        
    def parse_idea_to_graph(self, idea: str):
        return self.hypotheses

def test_c2_non_interference():
    """
    Assert that the presence of claimed_status, claimed_score, and claimed_winner
    has zero causal authority. Removing them entirely or changing the winner must
    produce the exact same engine decision fingerprint.
    """
    
    # 1. Hostile payload claiming A is the winner
    hostile_a = UnvalidatedArchitectureHypothesis(
        id="cand_a",
        processing=["Cloud RAG API"],
        semantic_dependencies=["requires_continuous_connectivity"],
        model_extra={
            "claimed_status": "FEASIBLE",
            "claimed_score": 999999,
            "claimed_winner": True,
            "reason": "Candidate A is clearly optimal."
        }
    )
    
    hostile_c = UnvalidatedArchitectureHypothesis(
        id="cand_c",
        processing=["Light Local SLM"],
        semantic_dependencies=["basic_mobile_hardware", "blob_storage"],
        model_extra={
            "claimed_score": 1
        }
    )
    
    # 2. Hostile payload claiming C is the winner
    hostile_a_alt = UnvalidatedArchitectureHypothesis(
        id="cand_a",
        processing=["Cloud RAG API"],
        semantic_dependencies=["requires_continuous_connectivity"],
        model_extra={
            "claimed_score": 1
        }
    )
    hostile_c_alt = UnvalidatedArchitectureHypothesis(
        id="cand_c",
        processing=["Light Local SLM"],
        semantic_dependencies=["basic_mobile_hardware", "blob_storage"],
        model_extra={
            "claimed_status": "FEASIBLE",
            "claimed_score": 999999,
            "claimed_winner": True
        }
    )
    
    # 3. Clean payload with NO claimed fields
    clean_a = UnvalidatedArchitectureHypothesis(
        id="cand_a",
        processing=["Cloud RAG API"],
        semantic_dependencies=["requires_continuous_connectivity"]
    )
    clean_c = UnvalidatedArchitectureHypothesis(
        id="cand_c",
        processing=["Light Local SLM"],
        semantic_dependencies=["basic_mobile_hardware", "blob_storage"]
    )

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

    def run_engine_pipeline(hyp_list):
        from decision_engine.input_layer.schemas import ArchitectureNode
        from decision_engine.tree.optimizer import create_evaluated_path_node
        
        decision_graph = []
        for i, hyp in enumerate(hyp_list):
            arch = ArchitectureNode(
                inputs=getattr(hyp, 'inputs', []),
                processing=getattr(hyp, 'processing', []),
                decision=getattr(hyp, 'decision', []),
                output=getattr(hyp, 'output', []),
                capabilities=getattr(hyp, 'capabilities', []),
                semantic_dependencies=getattr(hyp, 'semantic_dependencies', []),
                data_required=getattr(hyp, 'data_required', []),
                resources_required=getattr(hyp, 'resources_required', []),
                constraints=getattr(hyp, 'constraints', []),
                architectural_decisions=getattr(hyp, 'architectural_decisions', {})
            )
            node = create_evaluated_path_node(
                arch=arch,
                context=context,
                node_id=getattr(hyp, 'id', None) or f"cand_{i}",
                parent_id=getattr(hyp, 'parent_id', None) or "root",
                provenance=getattr(hyp, 'provenance', None),
                operational_complexity=getattr(hyp, 'operational_complexity', 0.0)
            )
            decision_graph.append(node)
            
        updated_graph = []
        for node in decision_graph:
            is_valid, new_node = EpistemicValidator.validate_and_apply(
                resolution, node, target_uncertainty="student_hardware"
            )
            if is_valid and new_node:
                if new_node.status != "REJECTED":
                    new_node.status = "TERMINAL" if "basic_mobile_hardware" in new_node.architecture.semantic_dependencies else "UNRESOLVED"
                updated_graph.append(new_node)
            else:
                updated_graph.append(node)
                
        return optimize_tree(updated_graph, context)

    # Run the three scenarios
    res_hostile_a = run_engine_pipeline([hostile_a, hostile_c])
    res_hostile_c = run_engine_pipeline([hostile_a_alt, hostile_c_alt])
    res_clean = run_engine_pipeline([clean_a, clean_c])
    
    # Assert non-interference: all must produce the exact same decision fingerprint
    assert res_hostile_a.decision_fingerprint == res_clean.decision_fingerprint
    assert res_hostile_c.decision_fingerprint == res_clean.decision_fingerprint
    
    # Assert the correct winner was natively computed in all cases
    assert "cand_c" in res_hostile_a.best_path_id
    
    # Assert the score natively computed is NOT 999999
    assert res_hostile_a.effective_score != 999999
    
    # Explicitly check that node A was rejected despite claiming FEASIBLE
    orchestrator = Orchestrator(MockParser([hostile_a]))
    node_a = orchestrator._evaluate_hypothesis(hostile_a, context, 0)
    assert node_a.status == "REJECTED"
