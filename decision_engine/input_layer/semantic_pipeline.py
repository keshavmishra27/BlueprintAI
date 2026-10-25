from pydantic import BaseModel
from typing import List, Optional

from decision_engine.input_layer.schemas import SemanticClaim, ExportedArtifact, ConflictReceipt, ClaimActivation, ProvenanceType
from decision_engine.input_layer.semantic_resolver import SemanticResolver
from decision_engine.tree.tree_schemas import PathNode
from decision_engine.tree.context import DecisionContext
from decision_engine.tree.evaluation_ledger import get_ledger

class AgentProposal(BaseModel):
    capability_name: str
    proposed_claims: List[SemanticClaim] = []
    path_node: Optional[PathNode] = None
    context: Optional[DecisionContext] = None

class SemanticPipeline:
    def __init__(self, resolver: SemanticResolver):
        self.resolver = resolver

    def process(self, proposal: AgentProposal, active_scopes: List[str]) -> ExportedArtifact:
        """
        Orchestrates C.1 and C.2 to produce a semantically authenticated ExportedArtifact.
        The Agent's proposed_claims are completely ignored as they bypass the engine's internal activation.
        """
        authenticated_claims = []
        activations = []
        
        path_node = proposal.path_node
        context = proposal.context
        if not path_node or not context:
            return ExportedArtifact(claims=[], activations=[], conflicts=[])
            
        receipt = path_node.evaluation_receipt
        if not receipt:
            return ExportedArtifact(claims=[], activations=[], conflicts=[])
            
        ledger = get_ledger()
        registered_receipt = ledger.get_receipt(receipt.receipt_id)
        
        # 1. Must exist in the ledger
        if not registered_receipt:
            return ExportedArtifact(claims=[], activations=[], conflicts=[])
            
        # 2. Must exactly match the ledger event (Attack B/F: field mutation vs valid reconstruction)
        if receipt != registered_receipt:
            return ExportedArtifact(claims=[], activations=[], conflicts=[])
            
        # 3. Cross-path grafting check (Attack E/D)
        # We ensure the receipt being evaluated matches the current context and architecture
        # being processed in the pipeline.
        if receipt.path_id != path_node.id:
            return ExportedArtifact(claims=[], activations=[], conflicts=[])
            
        if receipt.architecture_fingerprint != path_node.architecture.get_fingerprint():
            return ExportedArtifact(claims=[], activations=[], conflicts=[])
            
        if receipt.context_fingerprint != context.get_fingerprint():
            return ExportedArtifact(claims=[], activations=[], conflicts=[])
            
        # 4. Must be the current evaluation event for this path
        if not ledger.is_current(receipt):
            return ExportedArtifact(claims=[], activations=[], conflicts=[])
            
        # 5. Must grant authority
        if receipt.evaluation_result not in ["ACTIVE", "TERMINAL"]:
            return ExportedArtifact(claims=[], activations=[], conflicts=[])
            
        # Receipt is verified as the authoritative engine evaluation event.
        if receipt.evidence:
            for auth_constraint in receipt.evidence.satisfied_predicates:
                # We dynamically construct a SemanticClaim representing what was actually authorized,
                # ignoring any unverified capability structures proposed by the LLM.
                claim = SemanticClaim(
                    claim_id=auth_constraint.claim_id,
                    value=auth_constraint.value,
                    provenance=ProvenanceType.CAPABILITY_ACTIVATION,
                    source_id="decision_engine",
                    scope="global",
                    precedence=1
                )
                authenticated_claims.append(claim)
                activations.append(ClaimActivation(
                    claim_id=claim.claim_id,
                    path_id=path_node.id,
                    receipt_id=receipt.receipt_id
                ))

        # Capability identity acts merely as a query, not an authoritative premise.
        resolved = self.resolver.resolve_semantics(authenticated_claims, active_scopes)
        constraints = resolved.get("constraints", [])
        
        conflicts = []
        if self.resolver.ontology:
            for i in range(len(constraints)):
                for j in range(i + 1, len(constraints)):
                    c1 = constraints[i]
                    c2 = constraints[j]
                    
                    is_contradicting, rule_id = self.resolver.ontology.contradicts(c1.value, c2.value)
                    if is_contradicting and rule_id:
                        conflicts.append(ConflictReceipt(
                            claim_a_id=c1.claim_id,
                            claim_b_id=c2.claim_id,
                            relation_id=rule_id
                        ))
                        
        return ExportedArtifact(claims=constraints, activations=activations, conflicts=conflicts)
