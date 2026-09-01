from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Literal
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement, UserIdea, ArchitectureComparison
from idea_refiner.schema import RequirementArtifact
class ArchitectureState(BaseModel):
    architecture: ArchitectureNode
    generation: int
    based_on: Optional[str] = None

class ProjectState(BaseModel):
    user_idea: UserIdea
    current_constraints: List[str]
    current_requirements: List[Requirement]

class StateMutation(BaseModel):
    add_constraints: List[str]
    remove_constraints: List[str]

class AnswerOption(BaseModel):
    mutation: StateMutation
    candidate_architecture: Optional[ArchitectureNode] = None
    epistemic_resolutions: Dict[str, str] = {}

class BranchOutcome(BaseModel):
    b_feasible: bool
    winner: str
    architecture_name: str
    architecture_capabilities: List[str]
    b_dimensions: Optional[Dict[str, str]] = None

class UncertaintyImpact(BaseModel):
    feasibility_changed: bool
    winner_changed: bool
    architecture_changed: bool
    decision_impact_score: int

class ArchitecturalUncertainty(BaseModel):
    id: str
    question_target: str
    unknown_fact: str
    affected_architectures: List[str]
    possible_impacts: List[str]
    importance: str
    yes_outcome: Optional[BranchOutcome] = None
    no_outcome: Optional[BranchOutcome] = None
    impact_analysis: Optional[UncertaintyImpact] = None
    decision_impact_score: int = 0

class AgentUncertainty(BaseModel):
    id: str
    question_text: str
    question_target: str
    unknown_fact: str
    importance: str
    yes_mutation: StateMutation
    no_mutation: StateMutation
    yes_candidate_architecture: ArchitectureNode
    no_candidate_architecture: ArchitectureNode

class QuestionNode(BaseModel):
    id: str
    question_text: str
    uncertainty: ArchitecturalUncertainty
    options: Dict[str, AnswerOption]

class PathNode(BaseModel):
    id: str
    parent_id: Optional[str]
    architecture: ArchitectureNode
    question_that_produced_it: Optional[str] = None
    user_answer: Optional[str] = None
    state_mutation: List[str] = []
    dimension_evaluation: Optional[Dict[str, str]] = None
    path_cost: Optional[float] = None
    path_value: Optional[float] = None
    path_latency: Optional[float] = None
    path_timeline: Optional[float] = None
    path_score: Optional[float] = None
    operational_complexity: Optional[float] = None
    status: Literal["ACTIVE", "ALTERNATIVE", "REJECTED", "NEEDS_INFORMATION", "TERMINAL", "UNEXPLORED_HYPOTHESIS", "UNRESOLVED", "INVALID_CANDIDATE", "MAX_TURNS_REACHED"]
    reject_reasons: Optional[List[str]] = None
    selected_by_user: bool = False
    epistemic_provenance: Optional[Dict[str, Any]] = None
    epistemic_status: Optional[str] = None
    epistemic_evidence: Dict[str, str] = {}
    loop_identity_hash: Optional[str] = None
    uncertainty_target: Optional[str] = None

class TreeState(BaseModel):
    current_state_id: str
    project_state: ProjectState
    user_architecture: ArchitectureState
    player_b_architecture: ArchitectureState
    battle_history: List[ArchitectureComparison]
    decision_graph: List[PathNode] = []
    optimization_preferences: Optional[Dict[str, Any]] = None
    epistemic_requirements: Optional[RequirementArtifact] = None

class DecisionTraceEntry(BaseModel):
    question_text: str
    why_selected: str
    user_answer: str
    state_mutation: List[str]
    architecture_before: str
    architecture_after: str
    battle_before: str
    battle_after: str
