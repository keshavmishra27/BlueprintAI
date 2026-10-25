from typing import Dict, Set, Tuple, Optional
from decision_engine.input_layer.schemas import ArchitectureNode, SemanticClaim
from decision_engine.tree.context import AuthenticatedConstraint, AuthenticatedSemanticContext
from decision_engine.tree.evaluation_ledger import get_ledger
from decision_engine.input_layer.semantic_ontology import SemanticOntologyRegistry

# TYPE HINTING FOR CIRCULAR DEPENDENCY
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from decision_engine.tree.execution_capability import ExecutionCapability

_issued_capabilities: Dict[str, 'ExecutionCapability'] = {}

def _consume_capability(cap: 'ExecutionCapability', arch: ArchitectureNode) -> AuthenticatedSemanticContext:
    if cap.capability_id not in _issued_capabilities:
        raise AuthorityVerificationError("Forged capability ID")
    
    registered_cap = _issued_capabilities[cap.capability_id]
    if registered_cap is not cap:
        raise AuthorityVerificationError("Forged capability object (Identity mismatch)")
        
    if cap.authorized_architecture_fingerprint and cap.authorized_architecture_fingerprint != arch.get_authority_fingerprint():
        raise AuthorityVerificationError("Architecture mutation detected: authority-bearing fields modified after capability issuance.")
        
    # LIVE FRESHNESS CHECK
    ledger = get_ledger()
    for r_id in cap._context.relied_upon_receipts:
        if not ledger.is_current(ledger.get_receipt(r_id)):
            raise AuthorityVerificationError(f"Transitive receipt {r_id} has been revoked prior to consumption")
            
    # ONE-SHOT consumption ONLY UPON SUCCESS
    del _issued_capabilities[cap.capability_id]
            
    return cap._context

class AuthorityVerificationError(Exception):
    pass

class CyclicDerivationError(AuthorityVerificationError):
    pass

class ClaimCollisionError(AuthorityVerificationError):
    pass

class InvalidClaimStateError(AuthorityVerificationError):
    pass

class CanonicalizationError(AuthorityVerificationError):
    pass

class RuleIdentityError(AuthorityVerificationError):
    pass


def get_authorized_claims(arch: ArchitectureNode) -> Dict[str, SemanticClaim]:
    """
    Extracts the canonical claim set across all claim-bearing locations.
    Rule 13: Detect duplicate claim_ids. If contents differ, fail closed.
    """
    claims_map: Dict[str, SemanticClaim] = {}
    
    def _add_claim(c: SemanticClaim):
        if c.claim_id in claims_map:
            existing = claims_map[c.claim_id]
            if existing.model_dump() != c.model_dump():
                raise ClaimCollisionError(f"Duplicate claim_id with conflicting canonical contents: {c.claim_id}")
            # If they are exactly identical, we permit the duplicate structural reference.
        else:
            claims_map[c.claim_id] = c
            
    for cap in arch.capabilities:
        for c in cap.functional_properties:
            _add_claim(c)
        for c in cap.constraints:
            _add_claim(c)
            
    for c in arch.constraints:
        _add_claim(c)
        
    return claims_map


class AuthorityVerifier:
    def __init__(self, registry: SemanticOntologyRegistry):
        self.registry = registry
        
    def _verify_semantics(self, current_arch: ArchitectureNode) -> AuthenticatedSemanticContext:
        candidate_claims = get_authorized_claims(current_arch)
        verified_map: Dict[str, AuthenticatedConstraint] = {}
        visiting: Set[str] = set()
        receipts_used: Set[str] = set()
        
        def _verify_node(claim_id: str) -> AuthenticatedConstraint:
            if claim_id in visiting:
                raise CyclicDerivationError(f"Cycle detected at claim_id: {claim_id}")
            if claim_id in verified_map:
                return verified_map[claim_id]
                
            if claim_id not in candidate_claims:
                raise AuthorityVerificationError(f"Claim ID not found in candidate architecture: {claim_id}")
                
            claim = candidate_claims[claim_id]
            
            # Rule 12: Claim State Exclusivity
            is_leaf = claim.proof_receipt_id is not None and claim.derivation is None
            is_derived = claim.proof_receipt_id is None and claim.derivation is not None
            if not (is_leaf ^ is_derived):
                raise InvalidClaimStateError(f"Claim {claim_id} must be strictly LEAF or DERIVED.")
                
            visiting.add(claim_id)
            
            if is_leaf:
                ledger = get_ledger()
                receipt = ledger.get_receipt(claim.proof_receipt_id)
                if not receipt:
                    raise AuthorityVerificationError(f"Receipt not found: {claim.proof_receipt_id}")
                if not ledger.is_current(receipt):
                    raise AuthorityVerificationError(f"Receipt is no longer current: {claim.proof_receipt_id}")
                    
                hist_arch = ledger.get_historical_architecture(claim.proof_receipt_id)
                if not hist_arch:
                    raise CanonicalizationError(f"Historical architecture snapshot missing for receipt: {claim.proof_receipt_id}")
                    
                # Rule 14: Historical Snapshot Commitment
                if hist_arch.get_fingerprint() != receipt.architecture_fingerprint:
                    raise CanonicalizationError(f"Historical snapshot fingerprint does not match receipt: {claim.proof_receipt_id}")
                    
                hist_claims = get_authorized_claims(hist_arch)
                if claim_id not in hist_claims:
                    raise AuthorityVerificationError(f"Claim {claim_id} not found in historical architecture for receipt {claim.proof_receipt_id}")
                    
                hist_claim = hist_claims[claim_id]
                if hist_claim.value != claim.value:
                    raise AuthorityVerificationError(f"Claim value mismatch for {claim_id} against historical record")
                    
                receipts_used.add(claim.proof_receipt_id)
                trace = (f"Leaf Authorized by Receipt {receipt.receipt_id}",)
                verified_constraint = AuthenticatedConstraint(claim_id=claim_id, value=claim.value, authority_trace=trace)
                
            else: # is_derived
                parent_traces = []
                # Recursively verify parents
                for pid in claim.derivation.parent_claim_ids:
                    parent_constraint = _verify_node(pid)
                    parent_traces.extend(parent_constraint.authority_trace)
                    
                # Rule 11: Canonical Rule Identity
                # Find rule in registry
                rule = None
                for r in self.registry._rules:
                    if r.rule_id == claim.derivation.rule_id:
                        if r.get_hash() == claim.derivation.rule_hash:
                            rule = r
                            break
                if not rule:
                    raise RuleIdentityError(f"Immutable rule not found for rule_id={claim.derivation.rule_id} and hash={claim.derivation.rule_hash}")
                    
                # Ensure the derived value conceptually matches the rule target
                if claim.value != rule.target_concept:
                    raise AuthorityVerificationError(f"Derived value '{claim.value}' does not match rule target '{rule.target_concept}'")
                    
                trace = tuple(parent_traces + [f"Derived via {rule.rule_id} ({claim.derivation.rule_hash})"])
                verified_constraint = AuthenticatedConstraint(claim_id=claim_id, value=claim.value, authority_trace=trace)
                
            visiting.remove(claim_id)
            verified_map[claim_id] = verified_constraint
            return verified_constraint
            
        auth_func_props = []
        for cap in current_arch.capabilities:
            for c in cap.functional_properties:
                auth_func_props.append(_verify_node(c.claim_id))
                
        auth_constraints = []
        for c in current_arch.constraints:
            auth_constraints.append(_verify_node(c.claim_id))
            
        return AuthenticatedSemanticContext(
            context_id="",
            relied_upon_receipts=tuple(receipts_used),
            functional_properties=tuple(auth_func_props),
            constraints=tuple(auth_constraints)
        )
        
    def authorize_execution(self, current_arch: ArchitectureNode) -> 'ExecutionCapability':
        from decision_engine.tree.execution_capability import ExecutionCapability
        from decision_engine.input_layer.schemas import CandidateStatus
        
        # Check if architecture is fundamentally invalid/infeasible before issuing capability
        if current_arch.candidate_status in (CandidateStatus.INFEASIBLE, CandidateStatus.NO_CANDIDATE):
            raise AuthorityVerificationError(f"Cannot issue capability for invalid/infeasible branch status: {current_arch.candidate_status}")

        # Perform full verification
        ctx = self._verify_semantics(current_arch)
        
        import uuid
        cap_id = str(uuid.uuid4())
        
        # Create a new context with the assigned ID
        bound_ctx = AuthenticatedSemanticContext(
            context_id=cap_id,
            relied_upon_receipts=ctx.relied_upon_receipts,
            functional_properties=ctx.functional_properties,
            constraints=ctx.constraints
        )
        
        cap = ExecutionCapability(cap_id, bound_ctx, current_arch.get_authority_fingerprint())
        _issued_capabilities[cap_id] = cap
        return cap
