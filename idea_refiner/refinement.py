from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime

class RefinementArtifact(BaseModel):
    parent_decision_fingerprint: str
    parent_graph_fingerprint: str
    gap_report_fingerprint: str
    requirement_set_fingerprint: str
    
    # Constraints for LLM/Expander (NOT feasibility claims)
    preserved_decisions: List[str] = Field(description="Decisions that must be preserved due to MATCH")
    requested_changes: List[str] = Field(description="Targets for exploration due to MISSING/MISMATCH")
    unresolved_questions: List[str] = Field(description="Questions requiring investigation due to UNKNOWN")
    
    prohibited: List[str] = Field(default=["Silently claiming compliance without evidence", "Arbitrarily dropping requirements"], description="Prohibited actions")
    
    provenance: Dict[str, str] = Field(default_factory=lambda: {"source": "Deterministic Translator", "timestamp": datetime.utcnow().isoformat()})
