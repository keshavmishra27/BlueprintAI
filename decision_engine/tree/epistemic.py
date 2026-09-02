from typing import Dict, Any, Tuple, Optional
from decision_engine.tree.tree_schemas import PathNode
from idea_refiner.parsers.epistemic_resolver import EpistemicResolution

class InvalidResolutionError(Exception):
    pass

class EpistemicValidator:
    """
    Belongs to the Decision Engine. Authoritative validator of proposed epistemic resolutions.
    """
    
    # Mock ontology for M13-C0 proving purposes
    VALID_ONTOLOGY_MAPPINGS = {
        "student_hardware": {
            "low_end": "basic_mobile_hardware",
            "consumer_mobile": "consumer_mobile_hardware",
            "high_end": "high_end_hardware",
        }
    }
    
    @classmethod
    def validate_and_apply(
        cls, 
        resolution: EpistemicResolution, 
        active_node: PathNode,
        target_uncertainty: str
    ) -> Tuple[bool, Optional[PathNode]]:
        """
        Validates the proposed resolution against the ontology and active uncertainty,
        then derives a branch identity and attaches branch-local evidence.
        
        Returns:
            (is_valid, new_branch_node)
        """
        # 1. Validate Active Uncertainty
        if resolution.target != target_uncertainty:
            return False, None
            
        # 2. Validate Ontology
        valid_values = cls.VALID_ONTOLOGY_MAPPINGS.get(resolution.target)
        if not valid_values or resolution.normalized_value not in valid_values:
            return False, None
            
        # 3. Derive Branch Identity (The graph/engine owns this)
        branch_id = f"{active_node.id}_branch_{resolution.target}_{resolution.normalized_value}"
        
        # 4. Attach Branch-Local Evidence (preserving immutability of the parent)
        # We copy the parent node and append the resolved dependency.
        new_node = PathNode(**active_node.model_dump())
        new_node.id = branch_id
        new_node.parent_id = active_node.id
        
        # In a real ontology, we might map to a specific semantic dependency or constraint
        resolved_dependency = valid_values[resolution.normalized_value]
        if new_node.architecture:
            # We assume the architecture was waiting for this dependency or constraint to clear
            # For simplicity, we just add the resolved dependency. This could clear an UNRESOLVED state.
            new_node.architecture.semantic_dependencies.append(resolved_dependency)
            
        return True, new_node
