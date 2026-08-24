import sys
import copy
from pathlib import Path
from typing import List, Optional

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, UserIdea
from decision_engine.tree.tree_schemas import ProjectState, AgentUncertainty
from decision_engine.tree.experiment_llm_adapters import llm_baseline, llm_generate_player_b, llm_find_uncertainties

class AutomatedProtocolSimulator:
    """
    Automates the 'Agent Runtime' side of the Antigravity Level 6 experiment protocol.
    This component uses LLMs to generate hypotheses and architectures based purely on
    state updates, isolating generative intelligence from deterministic engine orchestration.
    """
    def __init__(self):
        self.evidence_context = "No previous evidence"

    def generate_initial_architecture(self, project_state: ProjectState) -> ArchitectureNode:
        print("[Simulator] LLM Generating initial architecture...")
        resp = llm_generate_player_b(project_state, self.evidence_context)
        return resp.architecture

    def find_uncertainties(self, architecture: ArchitectureNode, project_state: ProjectState) -> List[AgentUncertainty]:
        print("[Simulator] LLM Finding uncertainties...")
        return llm_find_uncertainties(architecture, project_state)

    def generate_adapted_architecture(self, 
                                      project_state: ProjectState, 
                                      previous_architecture: ArchitectureNode, 
                                      adaptation_reason: str) -> ArchitectureNode:
        print(f"[Simulator] LLM Generating adapted architecture due to: {adaptation_reason}")
        resp = llm_generate_player_b(project_state, self.evidence_context, previous_arch=previous_architecture, adaptation_reason=adaptation_reason)
        return resp.architecture
