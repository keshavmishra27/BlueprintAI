import pytest
from idea_refiner.schema import (
    RequirementArtifact,
    PredictionHorizon,
    LatencyRequirement,
    DataFreshnessRequirement,
    NetworkRequirement,
    DeploymentRequirement,
    Provenance,
    ProvenanceType,
    ConnectivityType
)
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.input_layer.epistemic_validator import (
    validate_epistemic_boundaries,
    EpistemicStatus
)

def build_unknown_requirements() -> RequirementArtifact:
    return RequirementArtifact(
        prediction_horizon=PredictionHorizon(
            id="R1", provenance=Provenance(type=ProvenanceType.UNKNOWN)
        ),
        latency=LatencyRequirement(
            id="R2", provenance=Provenance(type=ProvenanceType.UNKNOWN)
        ),
        data_freshness=DataFreshnessRequirement(
            id="R3", provenance=Provenance(type=ProvenanceType.UNKNOWN)
        ),
        network=NetworkRequirement(
            id="R4", provenance=Provenance(type=ProvenanceType.UNKNOWN)
        ),
        deployment=DeploymentRequirement(
            id="R5", provenance=Provenance(type=ProvenanceType.UNKNOWN)
        )
    )

def create_arch(deps: list[str]) -> ArchitectureNode:
    return ArchitectureNode(
        id="A1",
        name="Test",
        description="Test Arch",
        inputs=[],
        processing=[],
        decision=[],
        output=[],
        capabilities=[],
        semantic_dependencies=deps,
        data_required=[],
        resources_required=[],
        constraints=[],
        evidence_provenance=[]
    )

def test_not_applicable_aggregate():
    reqs = build_unknown_requirements()
    arch = create_arch(["requires_gpu", "paid_api"])
    status, reasons = validate_epistemic_boundaries(arch, reqs)
    assert status == EpistemicStatus.NOT_APPLICABLE

def test_unproven_dominates_not_applicable():
    reqs = build_unknown_requirements()
    arch = create_arch(["requires_gpu", "requires_continuous_connectivity"])
    status, reasons = validate_epistemic_boundaries(arch, reqs)
    assert status == EpistemicStatus.UNPROVEN

def test_contradiction_dominates_all():
    reqs = build_unknown_requirements()
    
    reqs = RequirementArtifact(
        prediction_horizon=reqs.prediction_horizon,
        latency=reqs.latency,
        data_freshness=DataFreshnessRequirement(
            id="R3",
            provenance=Provenance(type=ProvenanceType.EXPLICIT, source_quote="no realtime"),
            real_time_streams_required=False
        ),
        network=NetworkRequirement(
            id="R4",
            provenance=Provenance(type=ProvenanceType.EXPLICIT, source_quote="yes"),
            connectivity=ConnectivityType.CONTINUOUS
        ),
        deployment=reqs.deployment
    )
    
    arch = create_arch(["requires_continuous_connectivity", "requires_realtime_operational_data", "requires_gpu"])
    status, reasons = validate_epistemic_boundaries(arch, reqs)
    assert status == EpistemicStatus.CONTRADICTED

def test_unmapped_streaming_offline():
    reqs = build_unknown_requirements()
    reqs = RequirementArtifact(
        prediction_horizon=reqs.prediction_horizon,
        latency=reqs.latency,
        data_freshness=reqs.data_freshness,
        network=NetworkRequirement(
            id="R4",
            provenance=Provenance(type=ProvenanceType.EXPLICIT, source_quote="offline"),
            connectivity=ConnectivityType.OFFLINE
        ),
        deployment=reqs.deployment
    )
    arch = create_arch(["continuous_streaming"])
    status, reasons = validate_epistemic_boundaries(arch, reqs)
    assert status == EpistemicStatus.NOT_APPLICABLE

def test_satisfied_aggregate():
    reqs = build_unknown_requirements()
    reqs = RequirementArtifact(
        prediction_horizon=reqs.prediction_horizon,
        latency=reqs.latency,
        data_freshness=reqs.data_freshness,
        network=NetworkRequirement(
            id="R4",
            provenance=Provenance(type=ProvenanceType.EXPLICIT, source_quote="online"),
            connectivity=ConnectivityType.CONTINUOUS
        ),
        deployment=reqs.deployment
    )
    arch = create_arch(["requires_continuous_connectivity", "requires_gpu"])
    status, reasons = validate_epistemic_boundaries(arch, reqs)
    assert status == EpistemicStatus.SATISFIED

def test_empty_dependency_list():
    reqs = build_unknown_requirements()
    arch = create_arch([])
    status, reasons = validate_epistemic_boundaries(arch, reqs)
    assert status == EpistemicStatus.NOT_APPLICABLE
