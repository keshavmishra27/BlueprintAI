from pydantic import BaseModel
from typing import List
from decision_engine.api.artifact import CandidateEvaluation

class ExplanationFacts(BaseModel):
    candidates_evaluated: List[CandidateEvaluation]
    pareto_frontier_ids: List[str]
    winner_id: str
    governance_action: str
