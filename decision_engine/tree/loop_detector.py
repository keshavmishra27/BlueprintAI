import hashlib
import json
from typing import Dict, Any, List, Optional
from idea_refiner.schema import RequirementArtifact

def compute_epistemic_state_hash(
    question_target: str,
    epistemic_requirements: Optional[RequirementArtifact],
    epistemic_evidence: Dict[str, str],
    architecture_dependencies: List[str]
) -> str:
    """
    Computes a deterministic hash of the *relevant* epistemic state.
    This prevents harmless architecture changes from bypassing the loop detector,
    while correctly identifying when a semantic state has genuinely changed.
    """
    state_dict = {
        "target": question_target,
        "evidence": {k: epistemic_evidence[k] for k in sorted(epistemic_evidence.keys())},
        "dependencies": sorted(architecture_dependencies),
    }
    
    if epistemic_requirements:
        state_dict["requirements"] = epistemic_requirements.model_dump(exclude_none=True)
    else:
        state_dict["requirements"] = None
        
    canon_str = json.dumps(state_dict, sort_keys=True)
    return hashlib.sha256(canon_str.encode("utf-8")).hexdigest()

def detect_loop(
    current_target: str,
    current_requirements: Optional[RequirementArtifact],
    current_evidence: Dict[str, str],
    current_dependencies: List[str],
    decision_graph: List[Any],
    parent_node_id: Optional[str]
) -> bool:
    """
    Walks up the decision graph to check if the exact same semantic loop identity
    has been encountered in this branch.
    """
    current_hash = compute_epistemic_state_hash(
        current_target, current_requirements, current_evidence, current_dependencies
    )
    
    curr_id = parent_node_id
    while curr_id:
        node = next((n for n in decision_graph if n.id == curr_id), None)
        if not node:
            break
            
        if getattr(node, "loop_identity_hash", None):
            if node.loop_identity_hash == current_hash:
                return True
                
        curr_id = node.parent_id
        
    return False
