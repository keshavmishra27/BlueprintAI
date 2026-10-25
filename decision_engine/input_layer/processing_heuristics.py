from typing import List, Dict, Tuple, Optional, Any
from pydantic import BaseModel
import hashlib
import json
from decision_engine.input_layer.schemas import EvalStatus
from decision_engine.tree.context import AuthenticatedSemanticContext

class HeuristicDefinition(BaseModel):
    processing_id: str
    required_predicate_id: str
    required_predicate_location: str
    required_value: str
    native_score: float
    native_cost: float
    definition_hash: str = ""

    def compute_hash(self) -> str:
        data = {
            "processing_id": self.processing_id,
            "required_predicate_id": self.required_predicate_id,
            "required_predicate_location": self.required_predicate_location,
            "required_value": self.required_value,
            "native_score": float(self.native_score),
            "native_cost": float(self.native_cost)
        }
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def __init__(self, **data):
        super().__init__(**data)
        if not self.definition_hash:
            self.definition_hash = self.compute_hash()
        else:
            if self.definition_hash != self.compute_hash():
                raise ValueError(f"Tampered heuristic definition hash for {self.processing_id}")


# Immutable Registry (Closed-World)
_HEURISTIC_REGISTRY: Dict[str, HeuristicDefinition] = {
    "Cloud RAG API": HeuristicDefinition(
        processing_id="Cloud RAG API",
        required_predicate_id="network_capability",
        required_predicate_location="constraints",
        required_value="continuous",
        native_score=90.0,
        native_cost=40.0
    ),
    "High-End Local SLM": HeuristicDefinition(
        processing_id="High-End Local SLM",
        required_predicate_id="compute_capability",
        required_predicate_location="constraints",
        required_value="high_end",
        native_score=95.0,
        native_cost=10.0
    ),
    "Light Local SLM": HeuristicDefinition(
        processing_id="Light Local SLM",
        required_predicate_id="compute_capability",
        required_predicate_location="constraints",
        required_value="edge",
        native_score=85.0,
        native_cost=5.0
    )
}

def get_heuristic_definition(processing_id: str) -> Optional[HeuristicDefinition]:
    return _HEURISTIC_REGISTRY.get(processing_id)

def evaluate_processing_authorization(
    processing_choices: List[str],
    auth_context: AuthenticatedSemanticContext
) -> Tuple[EvalStatus, float, float, Optional[HeuristicDefinition], List[Any]]:
    """
    Evaluates the architecture processing choices against the authenticated semantic context.
    Returns (EvalStatus, best_score, best_cost).
    Strict causality:
    - Missing predicate -> UNKNOWN
    - Wrong/Conflicting predicate -> FAIL
    - Matches predicate exactly -> PASS
    """
    best_status = EvalStatus.UNKNOWN
    best_score = 50.0
    best_cost = 10.0
    
    if not processing_choices:
        return EvalStatus.UNKNOWN, best_score, best_cost, None, []

    for choice in processing_choices:
        heuristic = get_heuristic_definition(choice)
        
        if not heuristic:
            # Closed-world assumption
            # Unrecognized processing choice -> cannot be authorized
            return EvalStatus.UNKNOWN, 50.0, 10.0, None, []
            
        # Verify integrity
        if heuristic.definition_hash != heuristic.compute_hash():
            return EvalStatus.FAIL, 0.0, 0.0, None, []
            
        # Check auth_context
        # We look in the designated location
        if heuristic.required_predicate_location == "constraints":
            claims_to_check = auth_context.constraints
        elif heuristic.required_predicate_location == "functional_properties":
            claims_to_check = auth_context.functional_properties
        else:
            return EvalStatus.FAIL, 0.0, 0.0, None, []
            
        # Find all matching claims by ID
        matching_claims = [c for c in claims_to_check if c.claim_id == heuristic.required_predicate_id]
        
        if not matching_claims:
            # Missing predicate = UNKNOWN
            return EvalStatus.UNKNOWN, 50.0, 10.0, None, []
            
        # Check for conflicts
        unique_values = set(c.value for c in matching_claims)
        if len(unique_values) > 1:
            # Conflicting authenticated values = FAIL
            return EvalStatus.FAIL, 0.0, 0.0, None, []
            
        # Check if the single value matches the required value
        actual_value = matching_claims[0].value
        if actual_value != heuristic.required_value:
            # Known unsatisfied predicate = FAIL
            return EvalStatus.FAIL, 0.0, 0.0, None, []
            
        # Matches!
        return EvalStatus.PASS, heuristic.native_score, heuristic.native_cost, heuristic, matching_claims
        
    return EvalStatus.UNKNOWN, 50.0, 10.0, None, []
