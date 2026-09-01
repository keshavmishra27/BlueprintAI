from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class Governance(BaseModel):
    action: str
    severity: str
    scores: Dict[str, float] = Field(default_factory=dict)

class Component(BaseModel):
    name: str
    type: str
    description: Optional[str] = None

class Architecture(BaseModel):
    components: List[Component]
    decisions: List[Dict[str, Any]]

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

class Alternative(BaseModel):
    description: str
    architecture: Architecture

class Decision(BaseModel):
    id: str
    version: int
    architecture: Architecture
    governance: Governance
    alternatives: List[Alternative]
    
    winner_id: str = ""
    candidates_evaluated: List[CandidateEvaluation] = Field(default_factory=list)
    pareto_frontier_ids: List[str] = Field(default_factory=list)
    explanation: str = ""
    
    alignment: Optional[float] = None
    
    decision_fingerprint: str
    graph_fingerprint: str
    context_fingerprint: str
    requirement_set_fingerprint: str
    status: str
    created_at: datetime

class IdeaAnalyzeRequest(BaseModel):
    idea: str
    context: Optional[Dict[str, Any]] = None

class DecisionStatusUpdateRequest(BaseModel):
    status: str

class RepoAnalyzeRequest(BaseModel):
    decision_id: str
    repo_path: str

class GapReport(BaseModel):
    id: str
    decision_id: str
    decision_fingerprint: str
    requirement_set_fingerprint: str
    repository_fingerprint: str
    expected_architecture: Architecture
    actual_architecture: Dict[str, Any]
    findings: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    alignment_score: float
    created_at: datetime

class RefinementCreateRequest(BaseModel):
    decision_id: str
    gap_report_id: Optional[str] = None
    new_constraint: Optional[str] = None

class RefinementOption(BaseModel):
    problem_detected: str
    preserved: List[str]
    exploration: str

class RefinementCreateResponse(BaseModel):
    options: List[RefinementOption]

class RefinementApplyRequest(BaseModel):
    decision_id: str
    gap_report_id: Optional[str] = None
    applied_exploration: str
    preserved: List[str]
    problem_detected: str
