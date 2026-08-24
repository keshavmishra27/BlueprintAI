from pydantic import BaseModel
from typing import List

class AlternativeComparison(BaseModel):
    architecture_name: str
    status: str
    pros: List[str]
    cons: List[str]

class ExplanationFacts(BaseModel):
    winner_name: str
    winner_components: str
    performance: float
    cost: float
    robustness: float
    complexity: float
    epistemic_risk: int
    governance_action: str
    alternatives: List[AlternativeComparison]
