import pytest
from unittest.mock import patch

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
from decision_engine.input_layer.schemas import ArchitectureNode, UserIdea, ArchitectureComparison, Winner
from decision_engine.tree.tree_schemas import AgentUncertainty, StateMutation, TreeState, ProjectState
from backend.app.routers.journey import start_journey, JourneyStartRequest

def create_mock_artifact(network_connectivity=ConnectivityType.CONTINUOUS) -> RequirementArtifact:
    if network_connectivity is None:
        prov = Provenance(type=ProvenanceType.UNKNOWN)
        return RequirementArtifact(
            prediction_horizon=PredictionHorizon(id="r1", provenance=prov),
            latency=LatencyRequirement(id="r2", provenance=prov),
            data_freshness=DataFreshnessRequirement(id="r3", provenance=prov),
            network=NetworkRequirement(id="r4", provenance=prov),
            deployment=DeploymentRequirement(id="r5", provenance=prov)
        )
    else:
        prov_unknown = Provenance(type=ProvenanceType.UNKNOWN)
        prov_explicit = Provenance(type=ProvenanceType.EXPLICIT, source_quote="test")
        return RequirementArtifact(
            prediction_horizon=PredictionHorizon(id="r1", provenance=prov_unknown),
            latency=LatencyRequirement(id="r2", provenance=prov_unknown),
            data_freshness=DataFreshnessRequirement(id="r3", provenance=prov_unknown),
            network=NetworkRequirement(id="r4", provenance=prov_explicit, connectivity=network_connectivity),
            deployment=DeploymentRequirement(id="r5", provenance=prov_unknown)
        )

def create_mock_project_state() -> ProjectState:
    return ProjectState(
        user_idea=UserIdea(what="Test", why="Test", how_raw="Test", how_structured=ArchitectureNode()),
        current_constraints=[],
        current_requirements=[]
    )

def create_mock_uncertainty(target: str) -> AgentUncertainty:
    return AgentUncertainty(
        id="u1",
        question_text="Q?",
        question_target=target,
        unknown_fact="F",
        importance="HIGH",
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_candidate_architecture=ArchitectureNode(),
        no_candidate_architecture=ArchitectureNode()
    )

class TestM92Integration:

    @patch('backend.app.routers.journey.evaluate_speculative_battle')
    def test_1_explicit_compatible_dependency(self, mock_evaluate):
        artifact = create_mock_artifact(network_connectivity=ConnectivityType.CONTINUOUS)
        arch = ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"])
        req = JourneyStartRequest(
            session_id="t1",
            project_state=create_mock_project_state(),
            initial_architecture=arch,
            candidate_uncertainties=[],
            epistemic_requirements=artifact
        )
        
        mock_evaluate.return_value = ArchitectureComparison(b_feasible=True, a_feasible=True, winner=Winner.PLAYER_B, reasoning="test")
        
        with patch('backend.app.routers.journey.evaluate_provided_uncertainties', return_value=[]):
            start_journey(req)
        
        assert mock_evaluate.called

    @patch('backend.app.routers.journey.evaluate_speculative_battle')
    def test_2_explicit_contradiction(self, mock_evaluate):
        artifact = create_mock_artifact(network_connectivity=ConnectivityType.OFFLINE)
        arch = ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"])
        req = JourneyStartRequest(
            session_id="t2",
            project_state=create_mock_project_state(),
            initial_architecture=arch,
            candidate_uncertainties=[],
            epistemic_requirements=artifact
        )
        
        with patch('backend.app.routers.journey.evaluate_provided_uncertainties', return_value=[]):
            start_journey(req)
        
        assert not mock_evaluate.called
        from backend.app.routers.journey import sessions
        assert sessions["t2"].decision_graph[0].status == "REJECTED"

    @patch('backend.app.routers.journey.evaluate_speculative_battle')
    def test_3_unproven_with_matching_uncertainty(self, mock_evaluate):
        artifact = create_mock_artifact(network_connectivity=None)
        arch = ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"])
        req = JourneyStartRequest(
            session_id="t3",
            project_state=create_mock_project_state(),
            initial_architecture=arch,
            candidate_uncertainties=[create_mock_uncertainty("network.connectivity")],
            epistemic_requirements=artifact
        )
        
        with patch('backend.app.routers.journey.evaluate_provided_uncertainties', return_value=[]):
            start_journey(req)
            
        assert not mock_evaluate.called
        from backend.app.routers.journey import sessions
        assert sessions["t3"].decision_graph[0].status == "NEEDS_INFORMATION"

    @patch('backend.app.routers.journey.evaluate_speculative_battle')
    def test_4_unproven_with_no_matching_uncertainty(self, mock_evaluate):
        artifact = create_mock_artifact(network_connectivity=None)
        arch = ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"])
        req = JourneyStartRequest(
            session_id="t4",
            project_state=create_mock_project_state(),
            initial_architecture=arch,
            candidate_uncertainties=[create_mock_uncertainty("unrelated.dimension")],
            epistemic_requirements=artifact
        )
        
        with patch('backend.app.routers.journey.evaluate_provided_uncertainties', return_value=[]):
            start_journey(req)
            
        assert not mock_evaluate.called
        from backend.app.routers.journey import sessions
        assert sessions["t4"].decision_graph[0].status == "INVALID_CANDIDATE"

    @patch('backend.app.routers.journey.evaluate_speculative_battle')
    def test_5_only_unmapped_dependencies(self, mock_evaluate):
        artifact = create_mock_artifact()
        arch = ArchitectureNode(semantic_dependencies=["requires_gpu"])
        req = JourneyStartRequest(
            session_id="t5",
            project_state=create_mock_project_state(),
            initial_architecture=arch,
            candidate_uncertainties=[],
            epistemic_requirements=artifact
        )
        mock_evaluate.return_value = ArchitectureComparison(b_feasible=True, a_feasible=True, winner=Winner.PLAYER_B, reasoning="test")
        
        with patch('backend.app.routers.journey.evaluate_provided_uncertainties', return_value=[]):
            start_journey(req)
            
        assert mock_evaluate.called

    @patch('backend.app.routers.journey.evaluate_speculative_battle')
    def test_6_mixed_unproven_and_not_applicable(self, mock_evaluate):
        artifact = create_mock_artifact(network_connectivity=None)
        arch = ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity", "requires_gpu"])
        req = JourneyStartRequest(
            session_id="t6",
            project_state=create_mock_project_state(),
            initial_architecture=arch,
            candidate_uncertainties=[create_mock_uncertainty("network.connectivity")],
            epistemic_requirements=artifact
        )
        with patch('backend.app.routers.journey.evaluate_provided_uncertainties', return_value=[]):
            start_journey(req)
            
        assert not mock_evaluate.called
        from backend.app.routers.journey import sessions
        assert sessions["t6"].decision_graph[0].status == "NEEDS_INFORMATION"

    @patch('backend.app.routers.journey.evaluate_speculative_battle')
    def test_7_mixed_contradicted_and_unproven(self, mock_evaluate):
        prov = Provenance(type=ProvenanceType.UNKNOWN)
        artifact = RequirementArtifact(
            prediction_horizon=PredictionHorizon(id="r1", provenance=prov),
            latency=LatencyRequirement(id="r2", provenance=prov),
            data_freshness=DataFreshnessRequirement(id="r3", provenance=prov),
            network=NetworkRequirement(id="r4", provenance=Provenance(type=ProvenanceType.EXPLICIT, source_quote="t"), connectivity=ConnectivityType.OFFLINE),
            deployment=DeploymentRequirement(id="r5", provenance=prov)
        )
        arch = ArchitectureNode(semantic_dependencies=[
            "requires_continuous_connectivity",
            "requires_realtime_operational_data"
        ])
        req = JourneyStartRequest(
            session_id="t7",
            project_state=create_mock_project_state(),
            initial_architecture=arch,
            candidate_uncertainties=[create_mock_uncertainty("network.connectivity")],
            epistemic_requirements=artifact
        )
        with patch('backend.app.routers.journey.evaluate_provided_uncertainties', return_value=[]):
            start_journey(req)
            
        assert not mock_evaluate.called
        from backend.app.routers.journey import sessions
        assert sessions["t7"].decision_graph[0].status == "REJECTED"

    def test_8_branch_mutation_requirement_artifact_unchanged(self):
        from pydantic import ValidationError
        artifact = create_mock_artifact()
        
        try:
            artifact.network.connectivity = ConnectivityType.OFFLINE
            assert False, "Should raise an error when mutating a frozen artifact"
        except ValidationError:
            assert True

    @patch('backend.app.routers.journey.evaluate_speculative_battle')
    def test_10_legacy_mode(self, mock_evaluate):
        arch = ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"])
        req = JourneyStartRequest(
            session_id="t10",
            project_state=create_mock_project_state(),
            initial_architecture=arch,
            candidate_uncertainties=[],
            epistemic_requirements=None
        )
        mock_evaluate.return_value = ArchitectureComparison(b_feasible=True, a_feasible=True, winner=Winner.PLAYER_B, reasoning="test")
        
        with patch('backend.app.routers.journey.evaluate_provided_uncertainties', return_value=[]):
            start_journey(req)
            
        assert mock_evaluate.called
