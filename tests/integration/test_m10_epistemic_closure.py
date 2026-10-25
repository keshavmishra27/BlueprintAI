import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from decision_engine.tree.tree_schemas import ProjectState, ArchitectureNode, AgentUncertainty
from decision_engine.input_layer.schemas import UserIdea
from decision_engine.input_layer.epistemic_validator import EpistemicStatus, validate_epistemic_boundaries
from idea_refiner.schema import RequirementArtifact, ConnectivityType, NetworkRequirement, DataFreshnessRequirement, Provenance, ProvenanceType, PredictionHorizon, LatencyRequirement, DeploymentRequirement

client = TestClient(app)

def create_mock_project_state() -> ProjectState:
    return ProjectState(
        current_constraints=[],
        current_requirements=[],
        historical_decisions=[],
        user_idea=UserIdea(
            what="Test Idea",
            why="Testing",
            how_raw="",
            how_structured=ArchitectureNode()
        )
    )

def create_mock_uncertainty(target: str, q_text: str) -> AgentUncertainty:
    from decision_engine.tree.tree_schemas import StateMutation
    from decision_engine.input_layer.schemas import UnvalidatedArchitectureHypothesis
    return AgentUncertainty(
        id="unc_" + target,
        question_target=target,
        question_text=q_text,
        unknown_fact="some_fact",
        importance="high",
        decision_impact_score=10.0,
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_candidate_architecture=ArchitectureNode(),
        no_candidate_architecture=ArchitectureNode(),
        yes_hypothesis=UnvalidatedArchitectureHypothesis(),
        no_hypothesis=UnvalidatedArchitectureHypothesis()
    )

def _get_empty_reqs() -> RequirementArtifact:
    unknown_prov = Provenance(type=ProvenanceType.UNKNOWN)
    return RequirementArtifact(
        prediction_horizon=PredictionHorizon(id="req_ph", provenance=unknown_prov),
        latency=LatencyRequirement(id="req_lat", provenance=unknown_prov),
        data_freshness=DataFreshnessRequirement(id="req_df", provenance=unknown_prov),
        network=NetworkRequirement(id="req_net", provenance=unknown_prov),
        deployment=DeploymentRequirement(id="req_dep", provenance=unknown_prov)
    )

def test_m10_c_unknown_dependency():
    arch = ArchitectureNode(semantic_dependencies=["requires_unknown_feature"])
    reqs = _get_empty_reqs()
    status, deps = validate_epistemic_boundaries(arch, reqs)
    assert status == EpistemicStatus.INVALID_CANDIDATE
    assert "requires_unknown_feature" in deps

def test_m10_d_mixed_dependency():
    arch = ArchitectureNode(semantic_dependencies=[
        "requires_continuous_connectivity",
        "requires_unknown_feature",
        "requires_realtime_operational_data"
    ])
    reqs = _get_empty_reqs()
    reqs_dict = reqs.model_dump()
    reqs_dict["network"]["connectivity"] = ConnectivityType.OFFLINE.value
    reqs_dict["network"]["provenance"] = {"type": ProvenanceType.EXPLICIT.value, "source_quote": "test"}
    new_reqs = RequirementArtifact(**reqs_dict)
    
    status, deps = validate_epistemic_boundaries(arch, new_reqs)
    assert status == EpistemicStatus.CONTRADICTED
    assert "requires_continuous_connectivity" in deps

def test_m10_e_orthogonal_dependency():
    arch = ArchitectureNode(semantic_dependencies=["requires_gpu"])
    reqs = _get_empty_reqs()
    status, deps = validate_epistemic_boundaries(arch, reqs)
    assert status == EpistemicStatus.NOT_APPLICABLE
    assert "requires_gpu" in deps

def test_m10_a_and_b_journey_endpoint():
    start_req_a = {
        "session_id": "m10_session_a",
        "project_state": create_mock_project_state().model_dump(),
        "initial_architecture": ArchitectureNode(
            semantic_dependencies=["requires_continuous_connectivity"]
        ).model_dump(),
        "candidate_uncertainties": [
            create_mock_uncertainty("foobar", "Is foobar required?").model_dump()
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump()
    }
    
    start_resp_a = client.post("/api/journey/start", json=start_req_a)
    assert start_resp_a.status_code == 200
    
    state_resp_a = client.get("/api/journey/m10_session_a/state")
    root_id_a = state_resp_a.json()["decision_graph"][0]["id"]
    
    ans_m10_a = {
        "session_id": "m10_session_a",
        "parent_node_id": root_id_a,
        "answer": "YES",
        "generated_architecture": ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"]).model_dump(),
        "candidate_uncertainties": [
            create_mock_uncertainty("foobar", "Is foobar required?").model_dump()
        ],
        "is_user_selected": True,
        "epistemic_resolutions": {
            "foobar": "anything"
        }
    }
    
    resp_a = client.post("/api/journey/answer", json=ans_m10_a)
    assert resp_a.status_code == 400
    assert "Unknown ontology target: foobar" in resp_a.json()["detail"]
    
    start_req_b = {
        "session_id": "m10_session_b",
        "project_state": create_mock_project_state().model_dump(),
        "initial_architecture": ArchitectureNode(
            semantic_dependencies=["requires_continuous_connectivity"]
        ).model_dump(),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump()
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump()
    }
    
    start_resp_b = client.post("/api/journey/start", json=start_req_b)
    assert start_resp_b.status_code == 200
    
    state_resp_b = client.get("/api/journey/m10_session_b/state")
    root_id_b = state_resp_b.json()["decision_graph"][0]["id"]

    ans_m10_b = {
        "session_id": "m10_session_b",
        "parent_node_id": root_id_b,
        "answer": "YES",
        "generated_architecture": ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"]).model_dump(),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump()
        ],
        "is_user_selected": True,
        "epistemic_resolutions": {
            "network.connectivity": "hacked_value"
        }
    }
    
    resp_b = client.post("/api/journey/answer", json=ans_m10_b)
    assert resp_b.status_code == 400
    assert "Invalid value hacked_value for target network.connectivity" in resp_b.json()["detail"]
    assert "Invalid value hacked_value for target network.connectivity" in resp_b.json()["detail"]
