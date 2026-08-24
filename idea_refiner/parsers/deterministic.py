from typing import List
from decision_engine.tree.optimizer import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode
from .base import BaseIdeaParser

def create_mock_arch(deps):
    return ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=[], constraints=[],
        semantic_dependencies=list(deps),
        evidence_provenance=[],
        architectural_decisions={}
    )

class DeterministicIdeaParser(BaseIdeaParser):
    """
    Deterministic fixture adapter for Milestone 1 integration testing.
    """
    def parse_idea_to_graph(self, idea: str) -> List[PathNode]:
        # Always return a fixed decision graph based on the idea
        
        cand_a = PathNode(
            id="Cand_A", parent_id="root",
            architecture=create_mock_arch(["deps_A_ml"]),
            status="TERMINAL", path_score=100.0, path_cost=5.0, operational_complexity=2.0
        )
        cand_b_unres = PathNode(
            id="Cand_B", parent_id="root",
            architecture=create_mock_arch(["deps_B_stat"]),
            status="UNRESOLVED", path_score=150.0, path_cost=2.0, operational_complexity=1.0 
        )
        cand_c = PathNode(
            id="Cand_C", parent_id="root",
            architecture=create_mock_arch(["deps_C_heuristic"]),
            status="TERMINAL", path_score=60.0, path_cost=20.0, operational_complexity=10.0
        )
        
        if "unresolved" in idea.lower():
            # Cand_B dominates and is UNRESOLVED
            return [cand_a, cand_b_unres, cand_c]
        else:
            # Cand_A dominates and is TERMINAL
            cand_a.path_score = 150.0
            cand_a.path_cost = 2.0
            cand_a.operational_complexity = 1.0
            return [cand_a, cand_c]
