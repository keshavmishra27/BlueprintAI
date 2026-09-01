from enum import Enum
from typing import Tuple, List, Optional, Dict

from idea_refiner.schema import (
    RequirementArtifact, 
    ConnectivityType,
    ProvenanceType
)
from decision_engine.input_layer.schemas import ArchitectureNode

class EpistemicStatus(str, Enum):
    CONTRADICTED = "CONTRADICTED"
    UNPROVEN = "UNPROVEN"
    SATISFIED = "SATISFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INVALID_CANDIDATE = "INVALID_CANDIDATE"

KNOWN_ORTHOGONAL_DEPENDENCIES = {
    "requires_gpu",
    "requires_edge_gpu",
    "local_gpu_required",
    "paid_api",
    "commercial_cloud",
    "requires_cloud",
    "custom_hardware",
    "massive_data_collection",
    "continuous_streaming",
    "external_storage",
    "external_data_transfer",
    "requires_automatic_action",
    "autonomous_actions",
    "massive_custom_engineering",
    "vendor_lock_in",
    "requires_relational_db",
    "requires_cron_scheduling",
    "requires_event_streaming",
    "requires_cluster_compute",
    "requires_advanced_patient_tracking",
    "requires_ml",
    "requires_llm"
}

def validate_epistemic_boundaries(
    architecture: ArchitectureNode,
    requirements: RequirementArtifact,
    branch_evidence: Optional[Dict[str, str]] = None
) -> Tuple[EpistemicStatus, List[str]]:
    """
    Evaluates whether the architecture's semantic dependencies are compatible with 
    the immutable RequirementArtifact and any branch-local resolved evidence.
    
    Returns:
        Tuple[EpistemicStatus, List[str]]: The aggregate epistemic status and a list of reasons.
    """
    reasons = []
    statuses = []
    
    if not architecture.semantic_dependencies:
        return EpistemicStatus.NOT_APPLICABLE, []
        
    branch_evidence = branch_evidence or {}

    for dep in architecture.semantic_dependencies:
        if dep == "requires_continuous_connectivity":
            net_conn = branch_evidence.get("network.connectivity")
            if not net_conn and requirements.network.connectivity is not None:
                net_conn = requirements.network.connectivity.value
                
            if net_conn == ConnectivityType.CONTINUOUS.value:
                statuses.append((EpistemicStatus.SATISFIED, dep))
            elif net_conn == ConnectivityType.OFFLINE.value:
                statuses.append((EpistemicStatus.CONTRADICTED, dep))
            else:
                statuses.append((EpistemicStatus.UNPROVEN, dep))
                
        elif dep == "requires_realtime_operational_data":
            real_time = branch_evidence.get("data_freshness.real_time_streams_required")
            if real_time is None:
                real_time = requirements.data_freshness.real_time_streams_required
                
            if real_time is True or str(real_time).lower() == "true":
                statuses.append((EpistemicStatus.SATISFIED, dep))
            elif real_time is False or str(real_time).lower() == "false":
                statuses.append((EpistemicStatus.CONTRADICTED, dep))
            else:
                statuses.append((EpistemicStatus.UNPROVEN, dep))
        elif dep in KNOWN_ORTHOGONAL_DEPENDENCIES:
            statuses.append((EpistemicStatus.NOT_APPLICABLE, dep))
        else:
            statuses.append((EpistemicStatus.INVALID_CANDIDATE, dep))

    status_order = {
        EpistemicStatus.CONTRADICTED: 0,
        EpistemicStatus.INVALID_CANDIDATE: 1,
        EpistemicStatus.UNPROVEN: 2,
        EpistemicStatus.SATISFIED: 3,
        EpistemicStatus.NOT_APPLICABLE: 4
    }
    
    worst_status = min(statuses, key=lambda x: status_order[x[0]])[0]
    
    triggering_deps = [dep for status, dep in statuses if status == worst_status]
    
    return worst_status, triggering_deps
