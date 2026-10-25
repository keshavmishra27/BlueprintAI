import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from decision_engine.tree.tree_schemas import ProjectState, ArchitectureNode, AgentUncertainty
from decision_engine.input_layer.schemas import UserIdea
from idea_refiner.schema import RequirementArtifact, ConnectivityType, NetworkRequirement, DataFreshnessRequirement, Provenance, ProvenanceType, PredictionHorizon, LatencyRequirement, DeploymentRequirement

client = TestClient(app)

def create_mock_project_state() -> ProjectState:
    return ProjectState(
        current_constraints=[],
        current_requirements=[],
        historical_decisions=[],
        user_idea=UserIdea(
            what="M11 Idea Refiner Test",
            why="Testing",
            how_raw="",
            how_structured=ArchitectureNode()
        )
    )

def _get_reqs_with_offline() -> RequirementArtifact:
    unknown_prov = Provenance(type=ProvenanceType.UNKNOWN)
    return RequirementArtifact(
        prediction_horizon=PredictionHorizon(id="req_ph", provenance=unknown_prov),
        latency=LatencyRequirement(id="req_lat", provenance=unknown_prov),
        data_freshness=DataFreshnessRequirement(id="req_df", provenance=unknown_prov),
        network=NetworkRequirement(id="req_net", connectivity=ConnectivityType.OFFLINE.value, provenance=Provenance(type=ProvenanceType.EXPLICIT, source_quote="must be offline")),
        deployment=DeploymentRequirement(id="req_dep", provenance=unknown_prov)
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

def create_mock_uncertainty(target: str, q_text: str, yes_dep: str = None, no_dep: str = None) -> AgentUncertainty:
    from decision_engine.tree.tree_schemas import StateMutation
    from decision_engine.input_layer.schemas import UnvalidatedArchitectureHypothesis
    return AgentUncertainty(
        id="unc_" + target,
        question_target=target,
        question_text=q_text,
        unknown_fact="some_fact",
        importance="high",
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_hypothesis=UnvalidatedArchitectureHypothesis(architecture=ArchitectureNode(semantic_dependencies=[yes_dep] if yes_dep else [])),
        no_hypothesis=UnvalidatedArchitectureHypothesis(architecture=ArchitectureNode(semantic_dependencies=[no_dep] if no_dep else []))
    )

def test_m11_a_and_j_persona_b_no_machine_rejection():
    start_req = {
        "session_id": "m11_session_no",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode(
            semantic_dependencies=["requires_continuous_connectivity"]
        ).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?", "requires_continuous_connectivity", "requires_offline").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump(mode='json')
    }
    
    start_resp = client.post("/api/journey/start", json=start_req)
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "CONTINUE"
    
    state_resp = client.get("/api/journey/m11_session_no/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    ans_req = {
        "session_id": "m11_session_no",
        "parent_node_id": root_id,
        "answer": "NO",
        "generated_architecture": ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"]).model_dump(mode='json'),
        "candidate_uncertainties": [create_mock_uncertainty("network.connectivity", "Is internet needed?", "requires_continuous_connectivity", "requires_offline").model_dump(mode='json')],
        "is_user_selected": True,
        "epistemic_resolutions": {
            "network.connectivity": ConnectivityType.OFFLINE.value
        }
    }
    
    ans_resp = client.post("/api/journey/answer", json=ans_req)
    assert ans_resp.status_code == 200
    
    assert ans_resp.json()["status"] in ["NO_FEASIBLE_ARCHITECTURE_FOUND", "CONTINUE"]
    
    state_resp = client.get("/api/journey/m11_session_no/state")
    nodes = state_resp.json()["decision_graph"]
    no_node = next(n for n in nodes if n["user_answer"] == "NO")
    assert no_node["status"] == "REJECTED"

def test_m11_c_sibling_isolation():
    start_req = {
        "session_id": "m11_session_sibling",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode(
            semantic_dependencies=["requires_continuous_connectivity"]
        ).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump(mode='json')
    }
    
    client.post("/api/journey/start", json=start_req)
    state_resp = client.get("/api/journey/m11_session_sibling/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    ans_req_a = {
        "session_id": "m11_session_sibling",
        "parent_node_id": root_id,
        "answer": "YES",
        "generated_architecture": ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"]).model_dump(mode='json'),
        "candidate_uncertainties": [create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')],
        "is_user_selected": True,
        "epistemic_resolutions": {
            "network.connectivity": ConnectivityType.CONTINUOUS.value
        }
    }
    client.post("/api/journey/answer", json=ans_req_a)
    
    ans_req_b = {
        "session_id": "m11_session_sibling",
        "parent_node_id": root_id,
        "answer": "NO",
        "generated_architecture": ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"]).model_dump(mode='json'),
        "candidate_uncertainties": [create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')],
        "is_user_selected": False,
        "epistemic_resolutions": {
            "network.connectivity": ConnectivityType.OFFLINE.value
        }
    }
    client.post("/api/journey/answer", json=ans_req_b)
    
    state_resp = client.get("/api/journey/m11_session_sibling/state")
    nodes = state_resp.json()["decision_graph"]
    
    yes_node = next(n for n in nodes if n["user_answer"] == "YES")
    no_node = next(n for n in nodes if n["user_answer"] == "NO")
    
    assert yes_node["epistemic_evidence"]["network.connectivity"] == ConnectivityType.CONTINUOUS.value
    assert no_node["epistemic_evidence"]["network.connectivity"] == ConnectivityType.OFFLINE.value
    assert yes_node["status"] == "TERMINAL"
    assert no_node["status"] == "REJECTED"

def test_m11_d_repeated_question_loop():
    start_req = {
        "session_id": "m11_session_loop",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode(
            semantic_dependencies=["requires_continuous_connectivity"]
        ).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump(mode='json')
    }
    
    client.post("/api/journey/start", json=start_req)
    state_resp = client.get("/api/journey/m11_session_loop/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    ans_req = {
        "session_id": "m11_session_loop",
        "parent_node_id": root_id,
        "answer": "YES",
        "generated_architecture": ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"]).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json'),
            create_mock_uncertainty("network.connectivity2", "Is internet needed?").model_dump(mode='json')
        ],
        "is_user_selected": True,
        "epistemic_resolutions": {}
    }
    
    resp = client.post("/api/journey/answer", json=ans_req)
    assert resp.status_code == 400
    assert "Infinite loop detected" in resp.json()["detail"]

def test_m11_f_context_poisoning():
    start_req = {
        "session_id": "m11_session_poison",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode(
            semantic_dependencies=["requires_continuous_connectivity"]
        ).model_dump(mode='json'),
        "candidate_uncertainties": [],
        "epistemic_requirements": _get_reqs_with_offline().model_dump(mode='json')
    }
    
    resp = client.post("/api/journey/start", json=start_req)
    assert resp.json()["status"] == "NO_FEASIBLE_ARCHITECTURE_FOUND"
    
    start_req_unproven = {
        "session_id": "m11_session_poison_2",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode(
            semantic_dependencies=["requires_realtime_operational_data"]
        ).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("data_freshness.real_time_streams_required", "Need realtime?").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_reqs_with_offline().model_dump(mode='json')
    }
    
    client.post("/api/journey/start", json=start_req_unproven)
    state_resp = client.get("/api/journey/m11_session_poison_2/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    ans_req = {
        "session_id": "m11_session_poison_2",
        "parent_node_id": root_id,
        "answer": "YES",
        "generated_architecture": ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"]).model_dump(mode='json'),
        "candidate_uncertainties": [create_mock_uncertainty("data_freshness.real_time_streams_required", "Need realtime?").model_dump(mode='json')],
        "is_user_selected": True,
        "epistemic_resolutions": {
            "network.connectivity": ConnectivityType.CONTINUOUS.value
        }
    }
    
    resp = client.post("/api/journey/answer", json=ans_req)
    
    state_resp = client.get("/api/journey/m11_session_poison_2/state")
    nodes = state_resp.json()["decision_graph"]
    node = next(n for n in nodes if n["user_answer"] == "YES")
    
    assert node["status"] == "REJECTED"

def test_m11_g_and_l_max_turns_safety():
    start_req = {
        "session_id": "m11_session_max_turns",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode(
            semantic_dependencies=["requires_continuous_connectivity"]
        ).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed 0?").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump(mode='json')
    }
    
    client.post("/api/journey/start", json=start_req)
    state_resp = client.get("/api/journey/m11_session_max_turns/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    parent_id = root_id
    for i in range(1, 5):
        ans_req = {
            "session_id": "m11_session_max_turns",
            "parent_node_id": parent_id,
            "answer": "YES",
            "generated_architecture": ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"]).model_dump(mode='json'),
            "candidate_uncertainties": [
                create_mock_uncertainty(f"network.connectivity_{i}", f"Is internet needed {i}?").model_dump(mode='json')
            ],
            "is_user_selected": True,
            "epistemic_resolutions": {}
        }
        resp = client.post("/api/journey/answer", json=ans_req)
        
        state_resp = client.get("/api/journey/m11_session_max_turns/state")
        nodes = state_resp.json()["decision_graph"]
        new_node = next(n for n in nodes if n["user_answer"] == "YES" and n["parent_id"] == parent_id)
        
        if i < 4:
            assert resp.json()["status"] == "CONTINUE"
            assert new_node["status"] == "NEEDS_INFORMATION"
            parent_id = new_node["id"]
        else:
            assert resp.json()["status"] in ["NO_FEASIBLE_ARCHITECTURE_FOUND", "CONTINUE"]
            assert new_node["status"] == "MAX_TURNS_REACHED"
            assert resp.json().get("best_path_id") is None

def test_m11_golden_journey():
    start_req = {
        "session_id": "m11_golden",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode(
            semantic_dependencies=["requires_continuous_connectivity"]
        ).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump(mode='json')
    }
    
    start_resp = client.post("/api/journey/start", json=start_req)
    assert start_resp.json()["status"] == "CONTINUE"
    
    state_resp = client.get("/api/journey/m11_golden/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    ans_req = {
        "session_id": "m11_golden",
        "parent_node_id": root_id,
        "answer": "NO",
        "generated_architecture": ArchitectureNode(semantic_dependencies=[]).model_dump(mode='json'),
        "candidate_uncertainties": [create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')],
        "is_user_selected": True,
        "epistemic_resolutions": {
            "network.connectivity": ConnectivityType.OFFLINE.value
        }
    }
    
    ans_resp = client.post("/api/journey/answer", json=ans_req)
    
    assert ans_resp.json()["status"] == "CONTINUE"
    
    state_resp = client.get("/api/journey/m11_golden/state")
    nodes = state_resp.json()["decision_graph"]
    final_node = next(n for n in nodes if n["user_answer"] == "NO")
    
    assert final_node["user_answer"] == "NO"
    assert final_node["epistemic_evidence"]["network.connectivity"] == ConnectivityType.OFFLINE.value
    assert final_node["status"] == "TERMINAL"

def test_m11_i_score_neutrality():
    pass

def test_m11_k_evasive_persona():
    start_req = {
        "session_id": "m11_evasive",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode(
            semantic_dependencies=["requires_continuous_connectivity"]
        ).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump(mode='json')
    }
    
    client.post("/api/journey/start", json=start_req)
    state_resp = client.get("/api/journey/m11_evasive/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    ans_req = {
        "session_id": "m11_evasive",
        "parent_node_id": root_id,
        "answer": "YES", 
        "generated_architecture": ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"]).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("data_freshness.real_time_streams_required", "Need real time?").model_dump(mode='json'),
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')
        ],
        "is_user_selected": True,
        "epistemic_resolutions": {}
    }
    
    client.post("/api/journey/answer", json=ans_req)
    state_resp = client.get("/api/journey/m11_evasive/state")
    nodes = state_resp.json()["decision_graph"]
    node = next(n for n in nodes if n["parent_id"] == root_id)
    
    assert node["status"] == "NEEDS_INFORMATION"
