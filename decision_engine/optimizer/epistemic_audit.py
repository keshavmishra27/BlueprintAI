from typing import List
from pydantic import BaseModel
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.input_layer.ontology import get_known_dependencies

class EpistemicAuditResult(BaseModel):
    ontology_gaps_in_winning_architecture: List[str] = []
    requires_ontology_review: bool = False

def run_epistemic_audit(winning_architecture: ArchitectureNode) -> EpistemicAuditResult:
    """
    Evaluates the epistemic debt of a winning architecture.
    This is an observational audit and does not mutate the architecture.
    """
    known_deps = get_known_dependencies()
    gaps = [
        dep for dep in winning_architecture.semantic_dependencies
        if dep not in known_deps
    ]
    
    return EpistemicAuditResult(
        ontology_gaps_in_winning_architecture=gaps,
        requires_ontology_review=bool(gaps)
    )
