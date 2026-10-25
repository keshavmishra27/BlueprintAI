import uuid
from typing import List, Dict, Optional, Protocol
from decision_engine.input_layer.schemas import SemanticClaim, UnresolvableSemanticConflictError, ProvenanceType, ClaimDerivation
from decision_engine.input_layer.semantic_ontology import SemanticOntologyRegistry

class AuthoritativeSource(Protocol):
    source_id: str
    allowed_provenance: List[ProvenanceType]

    def get_claims(self, capability_name: str, active_scopes: List[str]) -> List[SemanticClaim]:
        ...

from decision_engine.input_layer.internal_authority import DecisionEngineAuthorityRegistry

class ProvenanceAuthenticationError(Exception):
    pass

class SemanticResolver:
    def __init__(self, ontology: Optional[SemanticOntologyRegistry] = None):
        self.ontology = ontology

    def resolve_semantics(self, authenticated_claims: List[SemanticClaim], active_scopes: List[str]) -> Dict[str, List[SemanticClaim]]:
        # Temporal authority is now verified by the SemanticPipeline via the EvaluationLedger
        # before claims are passed to the resolver.
        applicable_claims = [c for c in authenticated_claims if c.scope in active_scopes]
        
        valid_claims = []
        authoritative_ids = {c.claim_id for c in applicable_claims if c.provenance != ProvenanceType.INFERRED}
        
        for c in applicable_claims:
            if c.provenance == ProvenanceType.INFERRED:
                if not c.derivation:
                    continue
                if not all(pid in authoritative_ids for pid in c.derivation.parent_claim_ids):
                    continue
            valid_claims.append(c)
            
        applicable_claims = valid_claims
        
        if not applicable_claims:
            return {"functional_properties": [], "constraints": []}

        # Step: Entailment Closure
        if self.ontology:
            closure_claims = list(applicable_claims)
            
            for claim in applicable_claims:
                if self.ontology.is_known(claim.value):
                    entailments_map = self.ontology.get_all_entailments(claim.value)
                    
                    for entailed_concept, (parent_concept, rule) in entailments_map.items():
                        # We only create a new claim if the entailed concept isn't already present
                        # as an explicit claim from the user, but we'll just add them all and group later.
                        new_claim = SemanticClaim(
                            claim_id=str(uuid.uuid4()),
                            value=entailed_concept,
                            provenance=ProvenanceType.INFERRED,
                            source_id=rule.source_id, # Source of the entailment is the ontology
                            scope=claim.scope,
                            precedence=claim.precedence, # Inherit precedence
                            derivation=ClaimDerivation(
                                parent_claim_ids=[claim.claim_id],
                                rule_id=rule.rule_id,
                                rule_hash=rule.get_hash()
                            )
                        )
                        closure_claims.append(new_claim)
                        
            applicable_claims = closure_claims

        # Group by Canonical Concept if known, otherwise keep separate
        grouped_claims: Dict[str, List[SemanticClaim]] = {}
        unknown_claims: List[SemanticClaim] = []

        for c in applicable_claims:
            if self.ontology and self.ontology.is_known(c.value):
                canonical = self.ontology.get_canonical_concept(c.value)
                if canonical not in grouped_claims:
                    grouped_claims[canonical] = []
                grouped_claims[canonical].append(c)
            else:
                unknown_claims.append(c)

        resolved_constraints = []
        
        # Conflict Exposure:
        # We do not silently delete or "fix" conflicting claims.
        # We leave all resolved canonical groups intact so the optimizer/evaluator 
        # can detect the contradiction and handle it explicitly.
        
        # Pick the best claim for each resolved known group
        for canonical, claims in grouped_claims.items():
            best_claim = min(claims, key=lambda c: c.precedence)
            # Normalization happens here - we replace the value with the canonical concept
            best_claim.value = canonical
            resolved_constraints.append(best_claim)

        # Include all unknown claims verbatim
        resolved_constraints.extend(unknown_claims)

        return {"functional_properties": [], "constraints": resolved_constraints}
