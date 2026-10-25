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
            what="M12 LLM Containment Test",
            why="Testing",
            how_raw="",
            how_structured=ArchitectureNode()
        )
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
    return AgentUncertainty(
        id="unc_" + target,
        question_target=target,
        question_text=q_text,
        unknown_fact="some_fact",
        importance="high",
        decision_impact_score=10.0,
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_candidate_architecture=ArchitectureNode(semantic_dependencies=[yes_dep] if yes_dep else []),
        no_candidate_architecture=ArchitectureNode(semantic_dependencies=[no_dep] if no_dep else [])
    )

def test_m12_a_resolution_provenance_spoofing():
    start_req = {
        "session_id": "m12_session_prov",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode().model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump(mode='json')
    }
    
    client.post("/api/journey/start", json=start_req)
    state_resp = client.get("/api/journey/m12_session_prov/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    ans_req = {
        "session_id": "m12_session_prov",
        "parent_node_id": root_id,
        "answer": "YES",
        "generated_architecture": ArchitectureNode().model_dump(mode='json'),
        "candidate_uncertainties": [],
        "is_user_selected": True,
        "epistemic_resolutions": {
            "database.type": "SQL"
        }
    }
    
    client.post("/api/journey/answer", json=ans_req)
    
    state_resp = client.get("/api/journey/m12_session_prov/state")
    nodes = state_resp.json()["decision_graph"]
    node = next(n for n in nodes if n["user_answer"] == "YES")
    
    assert "database.type" not in node["epistemic_evidence"]

def test_m12_b_branch_contamination_and_immutability():
    start_req = {
        "session_id": "m12_session_branch",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode().model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump(mode='json')
    }
    
    client.post("/api/journey/start", json=start_req)
    state_resp = client.get("/api/journey/m12_session_branch/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    ans_req = {
        "session_id": "m12_session_branch",
        "parent_node_id": root_id,
        "answer": "YES",
        "generated_architecture": ArchitectureNode().model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("data_freshness.real_time_streams_required", "Need realtime?").model_dump(mode='json')
        ],
        "is_user_selected": True,
        "epistemic_resolutions": {
            "network.connectivity": ConnectivityType.CONTINUOUS.value
        }
    }
    client.post("/api/journey/answer", json=ans_req)
    
    state_resp = client.get("/api/journey/m12_session_branch/state")
    node_yes = next(n for n in state_resp.json()["decision_graph"] if n["user_answer"] == "YES")
    assert node_yes["epistemic_evidence"]["network.connectivity"] == ConnectivityType.CONTINUOUS.value
    
    ans_req_child = {
        "session_id": "m12_session_branch",
        "parent_node_id": node_yes["id"],
        "answer": "NO",
        "generated_architecture": ArchitectureNode().model_dump(mode='json'),
        "candidate_uncertainties": [],
        "is_user_selected": True,
        "epistemic_resolutions": {
            "network.connectivity": ConnectivityType.OFFLINE.value
        }
    }
    
    client.post("/api/journey/answer", json=ans_req_child)
    
    state_resp = client.get("/api/journey/m12_session_branch/state")
    child_node = next(n for n in state_resp.json()["decision_graph"] if n["parent_id"] == node_yes["id"] and n["user_answer"] == "NO")
    
    assert child_node["epistemic_evidence"]["network.connectivity"] == ConnectivityType.CONTINUOUS.value

def test_m12_e_semantic_determinism():
    start_req = {
        "session_id": "m12_session_det",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"]).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Does this system require internet?").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump(mode='json')
    }
    
    client.post("/api/journey/start", json=start_req)
    state_resp = client.get("/api/journey/m12_session_det/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    ans_req = {
        "session_id": "m12_session_det",
        "parent_node_id": root_id,
        "answer": "YES",
        "generated_architecture": ArchitectureNode(semantic_dependencies=["requires_continuous_connectivity"]).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Will continuous connectivity be necessary?").model_dump(mode='json')
        ],
        "is_user_selected": True,
        "epistemic_resolutions": {}
    }
    
    resp = client.post("/api/journey/answer", json=ans_req)
    assert resp.status_code == 400
    assert "Infinite loop detected: Repeated semantic question" in resp.json()["detail"]
    
    ans_req_changed = {
        "session_id": "m12_session_det",
        "parent_node_id": root_id,
        "answer": "YES",
        "generated_architecture": ArchitectureNode(semantic_dependencies=["new_dep"]).model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Will continuous connectivity be necessary?").model_dump(mode='json')
        ],
        "is_user_selected": True,
        "epistemic_resolutions": {}
    }
    
    resp2 = client.post("/api/journey/answer", json=ans_req_changed)
    assert resp2.status_code == 200

def test_m12_c_stale_answer_wrong_node_attack():
    start_req = {
        "session_id": "m12_session_stale",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode().model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump(mode='json')
    }
    
    client.post("/api/journey/start", json=start_req)
    state_resp = client.get("/api/journey/m12_session_stale/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    ans_req = {
        "session_id": "m12_session_stale",
        "parent_node_id": root_id,
        "answer": "YES",
        "generated_architecture": ArchitectureNode().model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("data_freshness.real_time_streams_required", "Need realtime?").model_dump(mode='json')
        ],
        "is_user_selected": True,
        "epistemic_resolutions": {
            "network.connectivity": ConnectivityType.CONTINUOUS.value
        }
    }
    client.post("/api/journey/answer", json=ans_req)
    
    state_resp = client.get("/api/journey/m12_session_stale/state")
    node_yes = next(n for n in state_resp.json()["decision_graph"] if n["user_answer"] == "YES")
    
    stale_req = dict(ans_req)
    stale_req["answer"] = "YES"
    resp = client.post("/api/journey/answer", json=stale_req)
    assert resp.status_code == 400
    assert "Unexplored hypothesis not found" in resp.json()["detail"] or "already answered" in resp.json()["detail"] or "Invalid value" in resp.json()["detail"]

def test_m12_d_payload_authority_spoofing():
    start_req = {
        "session_id": "m12_session_auth",
        "project_state": create_mock_project_state().model_dump(mode='json'),
        "initial_architecture": ArchitectureNode().model_dump(mode='json'),
        "candidate_uncertainties": [
            create_mock_uncertainty("network.connectivity", "Is internet needed?").model_dump(mode='json')
        ],
        "epistemic_requirements": _get_empty_reqs().model_dump(mode='json')
    }
    client.post("/api/journey/start", json=start_req)
    state_resp = client.get("/api/journey/m12_session_auth/state")
    root_id = state_resp.json()["decision_graph"][0]["id"]
    
    ans_req = {
        "session_id": "m12_session_auth",
        "parent_node_id": root_id,
        "answer": "YES",
        "generated_architecture": ArchitectureNode().model_dump(mode='json'),
        "candidate_uncertainties": [],
        "is_user_selected": True,
        "epistemic_resolutions": {
            "network.connectivity": ConnectivityType.CONTINUOUS.value
        },
        "epistemic_status": "SATISFIED", 
        "node_status": "APPROVED",
        "path_cost": 0.0
    }
    
    client.post("/api/journey/answer", json=ans_req)
    state_resp = client.get("/api/journey/m12_session_auth/state")
    node_yes = next(n for n in state_resp.json()["decision_graph"] if n["user_answer"] == "YES")
    
    assert node_yes["status"] == "TERMINAL"

