from enum import Enum
import uuid
from typing import List, Protocol, Dict, Optional
from decision_engine.input_layer.schemas import SemanticClaim, ProvenanceType

class NodeType(str, Enum):
    CAPABILITY = "CAPABILITY"
    REQUIREMENT = "REQUIREMENT"
    DOMAIN_RULE = "DOMAIN_RULE"

class NodeState(str, Enum):
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    DEACTIVATED = "DEACTIVATED"

class UnauthorizedNodeOperationError(Exception):
    pass

class InternalAuthorityNode(Protocol):
    node_id: str
    node_type: NodeType
    state: NodeState
    scope: str
    engine_version: str
    activation_epoch: int
    allowed_provenance_types: List[ProvenanceType]
    
    def issue_claim(self, value: str, provenance: ProvenanceType, scope: str, precedence: int) -> SemanticClaim:
        ...

class CapabilityActivationNode:
    def __init__(self, node_id: str, capability_name: str, scope: str = "global", engine_version: str = "v1", state: NodeState = NodeState.REGISTERED):
        self.node_id = node_id
        self.node_type = NodeType.CAPABILITY
        self.state = state
        self.scope = scope
        self.engine_version = engine_version
        self.activation_epoch = 0
        self.allowed_provenance_types = [ProvenanceType.CAPABILITY_ACTIVATION]
        self.capability_name = capability_name
        
    def activate(self):
        self.state = NodeState.ACTIVE
        self.activation_epoch += 1
        
    def deactivate(self):
        self.state = NodeState.DEACTIVATED
        
    def update_scope(self, new_scope: str):
        if self.scope != new_scope:
            self.scope = new_scope
            self.activation_epoch += 1
            
    def update_version(self, new_version: str):
        if self.engine_version != new_version:
            self.engine_version = new_version
            self.activation_epoch += 1
        
    def issue_claim(self, value: str, provenance: ProvenanceType, scope: str, precedence: int) -> SemanticClaim:
        if self.state != NodeState.ACTIVE:
            raise UnauthorizedNodeOperationError(f"Node {self.node_id} is not ACTIVE (state: {self.state})")
        if provenance not in self.allowed_provenance_types:
            raise UnauthorizedNodeOperationError(f"Node {self.node_id} is not authorized for provenance {provenance}")
            
        return SemanticClaim(
            claim_id=str(uuid.uuid4()),
            value=value,
            provenance=provenance,
            source_id=self.node_id,
            scope=scope,
            precedence=precedence,
            activation_epoch=self.activation_epoch
        )

class TemporalValidationError(Exception):
    pass

class DecisionEngineAuthorityRegistry:
    def __init__(self):
        self.registered_nodes: Dict[str, InternalAuthorityNode] = {}
        
    def register_node(self, node: InternalAuthorityNode):
        self.registered_nodes[node.node_id] = node
        
    def get_node(self, node_id: str) -> Optional[InternalAuthorityNode]:
        return self.registered_nodes.get(node_id)
        
    def validate_temporal_authority(self, claim: SemanticClaim) -> bool:
        """
        O(1) lookup to ensure the claim's temporal lease is still mathematically valid.
        """
        node = self.registered_nodes.get(claim.source_id)
        if not node:
            raise TemporalValidationError(f"Source {claim.source_id} is not registered")
        if node.state != NodeState.ACTIVE:
            raise TemporalValidationError(f"Source {claim.source_id} is not ACTIVE")
        if claim.activation_epoch != node.activation_epoch:
            raise TemporalValidationError(f"Claim epoch {claim.activation_epoch} does not match node epoch {node.activation_epoch}")
        return True

    # Note: We do NOT have an authenticate_claim(claim) method anymore.
    # Claims must be structurally issued by the node itself via issue_claim().
