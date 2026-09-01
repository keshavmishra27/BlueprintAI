from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DecisionMetrics(BaseModel):
    performance: float
    cost: float
    robustness: float
    complexity: float
    epistemic_risk: int

class CandidateEvaluation(BaseModel):
    candidate_id: str
    architecture_components: List[str]
    metrics: Optional[DecisionMetrics] = None
    status: Optional[str] = None

class ArchitectureDecisionArtifact(BaseModel):
    decision_id: str
    idea: str
    winner_id: str
    candidates_evaluated: List[CandidateEvaluation]
    pareto_frontier_ids: List[str]
    components: List[str]
    technologies: List[str]
    databases: List[str]
    interfaces: List[str]
    data_flows: List[str]
    decisions: Dict[str, str]
    constraints: List[str]
    dependencies: List[str]
    governance: Dict[str, Any]
    fingerprints: Dict[str, str]
    explanation: str
