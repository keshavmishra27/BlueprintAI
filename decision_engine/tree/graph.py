from enum import Enum
from typing import List, Dict, Optional, Any
import hashlib
from decision_engine.tree.tree_schemas import PathNode
from decision_engine.tree.context import canonicalize_json

class GraphState(str, Enum):
    GENERATING = "GENERATING"
    EXPANDED = "EXPANDED"
    VALIDATED = "VALIDATED"
    FROZEN = "FROZEN"

class FrozenGraphError(Exception):
    pass

class DecisionGraph:
    def __init__(self):
        self.state = GraphState.GENERATING
        self.nodes: Dict[str, PathNode] = {}
        self._fingerprint: Optional[str] = None
        
    def _assert_not_frozen(self):
        if self.state == GraphState.FROZEN:
            raise FrozenGraphError("Cannot mutate a FROZEN DecisionGraph.")
            
    def add_node(self, node: PathNode):
        self._assert_not_frozen()
        self.nodes[node.id] = node
        
    def remove_node(self, node_id: str):
        self._assert_not_frozen()
        if node_id in self.nodes:
            del self.nodes[node_id]
            
    def update_node_status(self, node_id: str, new_status: str):
        self._assert_not_frozen()
        if node_id in self.nodes:
            self.nodes[node_id].status = new_status

    def update_parent(self, node_id: str, new_parent_id: str):
        self._assert_not_frozen()
        if node_id in self.nodes:
            self.nodes[node_id].parent_id = new_parent_id
            
    def update_architecture(self, node_id: str, new_architecture: Any):
        self._assert_not_frozen()
        if node_id in self.nodes:
            self.nodes[node_id].architecture = new_architecture

    def transition_state(self, new_state: GraphState):
        self._assert_not_frozen()
        self.state = new_state
        if self.state == GraphState.FROZEN:
            self._fingerprint = self._compute_fingerprint()

    def freeze(self):
        self.transition_state(GraphState.FROZEN)

    def get_nodes(self) -> List[PathNode]:
        return list(self.nodes.values())
        
    def get_node(self, node_id: str) -> Optional[PathNode]:
        return self.nodes.get(node_id)

    def get_fingerprint(self) -> str:
        if self.state == GraphState.FROZEN:
            return self._fingerprint
        return self._compute_fingerprint()

    def _compute_fingerprint(self) -> str:
        graph_representation = []
        for node in sorted(self.nodes.values(), key=lambda x: x.id):
            deps = sorted(node.architecture.semantic_dependencies) if node.architecture else []
            node_rep = {
                "id": node.id,
                "parent_id": node.parent_id,
                "status": node.status,
                "path_score": node.path_score,
                "path_cost": node.path_cost,
                "operational_complexity": node.operational_complexity,
                "semantic_dependencies": deps,
                "architecture_fingerprint": node.architecture.get_fingerprint() if node.architecture else None
            }
            graph_representation.append(node_rep)
        canonical_str = canonicalize_json(graph_representation)
        return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
