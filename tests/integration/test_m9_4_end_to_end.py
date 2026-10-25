import pytest
from pydantic import ValidationError

from decision_engine.tree.tree_schemas import (
    ProjectState, 
    ArchitectureState, 
    PathNode, 
    TreeState, 
    StateMutation,
    AgentUncertainty,
    ArchitecturalUncertainty
)
from decision_engine.input_layer.schemas import ArchitectureNode, UserIdea
from decision_engine.input_layer.epistemic_validator import EpistemicStatus, validate_epistemic_boundaries
from idea_refiner.schema import (
    RequirementArtifact, 
    ConnectivityType, 
    ProvenanceType,
    Provenance,
    PredictionHorizon,
    LatencyRequirement,
    DataFreshnessRequirement,
    NetworkRequirement,
    DeploymentRequirement
)
from backend.app.routers.journey import start_journey, answer_journey, JourneyStartRequest, JourneyAnswerRequest, sessions

def setup_base_requirements() -> RequirementArtifact:
    return RequirementArtifact(
        prediction_horizon=PredictionHorizon(
            id="REQ-01", 
            provenance=Provenance(type=ProvenanceType.UNKNOWN)
        ),
        latency=LatencyRequirement(
            id="REQ-02", 
            provenance=Provenance(type=ProvenanceType.UNKNOWN)
        ),
        data_freshness=DataFreshnessRequirement(
            id="REQ-03", 
            provenance=Provenance(type=ProvenanceType.UNKNOWN)
        ),
        network=NetworkRequirement(
            id="REQ-04", 
            provenance=Provenance(type=ProvenanceType.UNKNOWN)
        ),
        deployment=DeploymentRequirement(
            id="REQ-05", 
            provenance=Provenance(type=ProvenanceType.UNKNOWN)
        )
    )

def setup_project_state() -> ProjectState:
    return ProjectState(
        user_idea=UserIdea(
            original_text="Mobile app",
            what="Tracking workouts",
            why="To stay fit",
            how_raw="Using a mobile phone",
            how_structured=ArchitectureNode(processing=[], capabilities=[], semantic_dependencies=[])
        ),
        current_constraints=[],
        current_requirements=[]
    )

def test_1_full_satisfied_path():
    reqs = setup_base_requirements()
    
    reqs = RequirementArtifact(
        prediction_horizon=reqs.prediction_horizon,
        latency=reqs.latency,
        data_freshness=reqs.data_freshness,
        network=NetworkRequirement(
            id="REQ-04",
            provenance=Provenance(type=ProvenanceType.EXPLICIT, source_quote="continuous internet"),
            connectivity=ConnectivityType.CONTINUOUS
        ),
        deployment=reqs.deployment
    )
    
    arch = ArchitectureNode(
        processing=["mobile_app"],
        capabilities=["workout_tracking"],
        semantic_dependencies=["requires_continuous_connectivity"]
    )
    
    req = JourneyStartRequest(
        session_id="test_1_full_satisfied",
        project_state=setup_project_state(),
        initial_architecture=arch,
        candidate_uncertainties=[],
        epistemic_requirements=reqs
    )
    
    resp = start_journey(req)
    
    assert resp.status == "TERMINAL"
    tree = sessions["test_1_full_satisfied"]
    root = tree.decision_graph[0]
    
    assert root.epistemic_status == "SATISFIED"
    assert root.path_score is not None

def test_2_full_not_applicable_path():
    reqs = setup_base_requirements() 
    
    arch = ArchitectureNode(
        processing=["mobile_app"],
        capabilities=["workout_tracking"],
        semantic_dependencies=[] 
    )
    
    req = JourneyStartRequest(
        session_id="test_2_full_na",
        project_state=setup_project_state(),
        initial_architecture=arch,
        candidate_uncertainties=[],
        epistemic_requirements=reqs
    )
    
    resp = start_journey(req)
    tree = sessions["test_2_full_na"]
    root = tree.decision_graph[0]
    
    assert root.epistemic_status == "NOT_APPLICABLE"
    assert root.path_score is not None

def test_3_full_unproven_uncertainty():
    reqs = setup_base_requirements()
    
    arch = ArchitectureNode(
        processing=["mobile_app"],
        capabilities=["workout_tracking"],
        semantic_dependencies=["requires_continuous_connectivity"]
    )
    
    unc = AgentUncertainty(
        id="unc_1",
        question_text="Is it offline?",
        question_target="network.connectivity",
        unknown_fact="connectivity",
        importance="high",
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_candidate_architecture=arch,
        no_candidate_architecture=arch
    )
    
    req = JourneyStartRequest(
        session_id="test_3_unproven_unc",
        project_state=setup_project_state(),
        initial_architecture=arch,
        candidate_uncertainties=[unc],
        epistemic_requirements=reqs
    )
    
    resp = start_journey(req)
    tree = sessions["test_3_unproven_unc"]
    root = tree.decision_graph[0]
    
    assert root.status == "NEEDS_INFORMATION"
    assert root.epistemic_status == "UNPROVEN"
    assert root.path_score is None 
    assert resp.status == "CONTINUE" 

def test_4_full_unproven_no_uncertainty():
    reqs = setup_base_requirements()
    arch = ArchitectureNode(
        processing=["mobile_app"],
        capabilities=["workout_tracking"],
        semantic_dependencies=["requires_continuous_connectivity"]
    )
    
    req = JourneyStartRequest(
        session_id="test_4_invalid",
        project_state=setup_project_state(),
        initial_architecture=arch,
        candidate_uncertainties=[], 
        epistemic_requirements=reqs
    )
    
    resp = start_journey(req)
    tree = sessions["test_4_invalid"]
    root = tree.decision_graph[0]
    
    assert root.status == "INVALID_CANDIDATE"
    assert root.path_score is None

def test_5_full_contradicted():
    reqs = setup_base_requirements()
    reqs = RequirementArtifact(
        prediction_horizon=reqs.prediction_horizon,
        latency=reqs.latency,
        data_freshness=reqs.data_freshness,
        network=NetworkRequirement(
            id="REQ-04",
            provenance=Provenance(type=ProvenanceType.EXPLICIT, source_quote="offline"),
            connectivity=ConnectivityType.OFFLINE
        ),
        deployment=reqs.deployment
    )
    
    arch = ArchitectureNode(
        processing=["mobile_app"],
        capabilities=["workout_tracking"],
        semantic_dependencies=["requires_continuous_connectivity"]
    )
    
    req = JourneyStartRequest(
        session_id="test_5_contradicted",
        project_state=setup_project_state(),
        initial_architecture=arch,
        candidate_uncertainties=[],
        epistemic_requirements=reqs
    )
    
    resp = start_journey(req)
    tree = sessions["test_5_contradicted"]
    root = tree.decision_graph[0]
    
    assert root.status == "REJECTED"
    assert root.epistemic_status == "CONTRADICTED"
    assert root.path_score is None

def test_6_immutability():
    reqs = setup_base_requirements()
    with pytest.raises(ValidationError):
        reqs.network = NetworkRequirement(
            id="REQ-04",
            provenance=Provenance(type=ProvenanceType.UNKNOWN),
            connectivity=ConnectivityType.CONTINUOUS
        )

def test_7_the_capstone_proof():
    reqs = setup_base_requirements()
    arch = ArchitectureNode(
        processing=["mobile_app"],
        capabilities=["workout_tracking"],
        semantic_dependencies=["requires_continuous_connectivity"]
    )
    
    unc = AgentUncertainty(
        id="unc_network",
        question_text="Is it offline?",
        question_target="network.connectivity",
        unknown_fact="connectivity",
        importance="high",
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_candidate_architecture=arch,
        no_candidate_architecture=arch
    )
    
    start_req = JourneyStartRequest(
        session_id="test_7_capstone",
        project_state=setup_project_state(),
        initial_architecture=arch,
        candidate_uncertainties=[unc],
        epistemic_requirements=reqs
    )
    start_journey(start_req)
    
    tree = sessions["test_7_capstone"]
    root = tree.decision_graph[0]
    
    assert root.status == "NEEDS_INFORMATION"
    assert root.epistemic_status == "UNPROVEN"
    
    ans_req = JourneyAnswerRequest(
        session_id="test_7_capstone",
        parent_node_id=root.id,
        answer="YES",
        generated_architecture=arch,
        candidate_uncertainties=[unc],
        is_user_selected=True,
        epistemic_resolutions={
            "network.connectivity": "continuous"
        }
    )
    
    answer_journey(ans_req)
    child = next(n for n in tree.decision_graph if n.parent_id == root.id and n.user_answer == "YES" and n.status != "UNEXPLORED_HYPOTHESIS")
    
    assert tree.epistemic_requirements.network.connectivity is None
    assert child.epistemic_evidence.get("network.connectivity") == "continuous"
    assert child.epistemic_status == "SATISFIED"
    assert child.status in ("ACTIVE", "TERMINAL", "CONTINUE", "UNRESOLVED")
    assert child.path_score is not None

def test_13_adversarial_inverse_unauthorized():
    reqs = setup_base_requirements()
    arch = ArchitectureNode(
        processing=["mobile_app"],
        capabilities=["workout_tracking"],
        semantic_dependencies=["requires_continuous_connectivity"]
    )
    
    unc_db = AgentUncertainty(
        id="unc_db",
        question_text="Database type?",
        question_target="database.type",
        unknown_fact="db",
        importance="high",
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_candidate_architecture=arch,
        no_candidate_architecture=arch
    )
    
    start_req = JourneyStartRequest(
        session_id="test_13_adversarial",
        project_state=setup_project_state(),
        initial_architecture=arch,
        candidate_uncertainties=[unc_db], 
        epistemic_requirements=reqs
    )
    start_journey(start_req)
    
    tree = sessions["test_13_adversarial"]
    root = tree.decision_graph[0]
    
    assert root.status == "INVALID_CANDIDATE"
    
    ans_req = JourneyAnswerRequest(
        session_id="test_13_adversarial",
        parent_node_id=root.id,
        answer="YES",
        generated_architecture=arch,
        candidate_uncertainties=[unc_db], 
        epistemic_resolutions={
            "network.connectivity": "continuous" 
        }
    )
    
    answer_journey(ans_req)
    child = next(n for n in tree.decision_graph if n.parent_id == root.id and n.user_answer == "YES" and n.status != "UNEXPLORED_HYPOTHESIS")
    
    assert "network.connectivity" not in child.epistemic_evidence
    assert child.epistemic_status == "UNPROVEN"
    assert child.status == "INVALID_CANDIDATE"

def test_14_sibling_isolation():
    reqs = setup_base_requirements()
    arch = ArchitectureNode(
        processing=["mobile_app"],
        capabilities=["workout_tracking"],
        semantic_dependencies=["requires_continuous_connectivity"]
    )
    
    unc = AgentUncertainty(
        id="unc_network",
        question_text="Is it offline?",
        question_target="network.connectivity",
        unknown_fact="connectivity",
        importance="high",
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_candidate_architecture=arch,
        no_candidate_architecture=arch
    )
    
    start_req = JourneyStartRequest(
        session_id="test_14_isolation",
        project_state=setup_project_state(),
        initial_architecture=arch,
        candidate_uncertainties=[unc],
        epistemic_requirements=reqs
    )
    start_journey(start_req)
    
    tree = sessions["test_14_isolation"]
    root = tree.decision_graph[0]
    
    ans_req_a = JourneyAnswerRequest(
        session_id="test_14_isolation",
        parent_node_id=root.id,
        answer="YES",
        generated_architecture=arch,
        candidate_uncertainties=[unc],
        is_user_selected=True,
        epistemic_resolutions={"network.connectivity": "continuous"}
    )
    answer_journey(ans_req_a)
    child_a = next(n for n in tree.decision_graph if n.parent_id == root.id and n.user_answer == "YES" and n.status != "UNEXPLORED_HYPOTHESIS")
    
    ans_req_b = JourneyAnswerRequest(
        session_id="test_14_isolation",
        parent_node_id=root.id,
        answer="NO",
        generated_architecture=arch,
        candidate_uncertainties=[unc],
        is_user_selected=True,
        epistemic_resolutions={"network.connectivity": "offline"}
    )
    answer_journey(ans_req_b)
    child_b = next(n for n in tree.decision_graph if n.parent_id == root.id and n.user_answer == "NO" and n.status != "UNEXPLORED_HYPOTHESIS")
    
    assert child_a.epistemic_evidence.get("network.connectivity") == "continuous"
    assert child_a.epistemic_status == "SATISFIED"
    
    assert child_b.epistemic_evidence.get("network.connectivity") == "offline"
    assert child_b.epistemic_status == "CONTRADICTED"
    assert child_b.status == "REJECTED"
    
    assert tree.epistemic_requirements.network.connectivity is None

def test_15_multilevel_inheritance():
    reqs = setup_base_requirements()
    arch = ArchitectureNode(
        processing=["mobile_app"],
        capabilities=["workout_tracking"],
        semantic_dependencies=["requires_continuous_connectivity"]
    )
    
    unc = AgentUncertainty(
        id="unc_network",
        question_text="Is it offline?",
        question_target="network.connectivity",
        unknown_fact="connectivity",
        importance="high",
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_candidate_architecture=arch,
        no_candidate_architecture=arch
    )
    
    start_req = JourneyStartRequest(
        session_id="test_15_multilevel",
        project_state=setup_project_state(),
        initial_architecture=arch,
        candidate_uncertainties=[unc],
        epistemic_requirements=reqs
    )
    start_journey(start_req)
    
    tree = sessions["test_15_multilevel"]
    root = tree.decision_graph[0]
    
    ans_req_1 = JourneyAnswerRequest(
        session_id="test_15_multilevel",
        parent_node_id=root.id,
        answer="YES",
        generated_architecture=arch,
        candidate_uncertainties=[unc],
        epistemic_resolutions={"network.connectivity": "continuous"}
    )
    answer_journey(ans_req_1)
    l1_node = next(n for n in tree.decision_graph if n.parent_id == root.id and n.user_answer == "YES" and n.status != "UNEXPLORED_HYPOTHESIS")
    
    assert l1_node.epistemic_evidence.get("network.connectivity") == "continuous"
    
    tree.decision_graph = [n for n in tree.decision_graph if not (n.parent_id == l1_node.id and n.status == "UNEXPLORED_HYPOTHESIS")]
    
    unc2 = AgentUncertainty(
        id="unc_db",
        question_text="Real time?",
        question_target="data_freshness.real_time_streams_required",
        unknown_fact="real_time",
        importance="high",
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_candidate_architecture=arch,
        no_candidate_architecture=arch
    )
    
    hypo = PathNode(
        id="hypo_2",
        parent_id=l1_node.id,
        architecture=arch,
        status="UNEXPLORED_HYPOTHESIS",
        question_that_produced_it="Real time?",
        user_answer="YES"
    )
    tree.decision_graph.append(hypo)
    
    ans_req_2 = JourneyAnswerRequest(
        session_id="test_15_multilevel",
        parent_node_id=l1_node.id,
        answer="YES",
        generated_architecture=arch,
        candidate_uncertainties=[unc2],
        epistemic_resolutions={"data_freshness.real_time_streams_required": "True"}
    )
    answer_journey(ans_req_2)
    l2_node = next(n for n in tree.decision_graph if n.parent_id == l1_node.id and n.user_answer == "YES" and n.status != "UNEXPLORED_HYPOTHESIS")
    
    assert l2_node.epistemic_evidence.get("network.connectivity") == "continuous"
    assert str(l2_node.epistemic_evidence.get("data_freshness.real_time_streams_required")).lower() == "true"
    assert l2_node.epistemic_status == "SATISFIED"

def test_16_contradiction_against_branch_evidence():
    reqs = setup_base_requirements()
    arch = ArchitectureNode(
        processing=["mobile_app"],
        capabilities=["workout_tracking"],
        semantic_dependencies=["requires_continuous_connectivity"]
    )
    
    unc = AgentUncertainty(
        id="unc_network",
        question_text="Is it offline?",
        question_target="network.connectivity",
        unknown_fact="connectivity",
        importance="high",
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_candidate_architecture=arch,
        no_candidate_architecture=arch
    )
    
    start_req = JourneyStartRequest(
        session_id="test_16_contradiction",
        project_state=setup_project_state(),
        initial_architecture=arch,
        candidate_uncertainties=[unc],
        epistemic_requirements=reqs
    )
    start_journey(start_req)
    
    tree = sessions["test_16_contradiction"]
    root = tree.decision_graph[0]
    
    ans_req = JourneyAnswerRequest(
        session_id="test_16_contradiction",
        parent_node_id=root.id,
        answer="NO",
        generated_architecture=arch,
        candidate_uncertainties=[unc],
        epistemic_resolutions={"network.connectivity": "offline"}
    )
    answer_journey(ans_req)
    child = next(n for n in tree.decision_graph if n.parent_id == root.id and n.user_answer == "NO" and n.status != "UNEXPLORED_HYPOTHESIS")
    
    assert child.epistemic_status == "CONTRADICTED"
    assert child.status == "REJECTED"

def test_17_adversarial_invalid_value_injection():
    reqs = setup_base_requirements()
    arch = ArchitectureNode(
        processing=["mobile_app"],
        capabilities=["workout_tracking"],
        semantic_dependencies=["requires_continuous_connectivity"]
    )
    
    unc = AgentUncertainty(
        id="unc_network",
        question_text="Is it offline?",
        question_target="network.connectivity",
        unknown_fact="connectivity",
        importance="high",
        yes_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        no_mutation=StateMutation(add_constraints=[], remove_constraints=[]),
        yes_candidate_architecture=arch,
        no_candidate_architecture=arch
    )
    
    start_req = JourneyStartRequest(
        session_id="test_17_adversarial_value",
        project_state=setup_project_state(),
        initial_architecture=arch,
        candidate_uncertainties=[unc],
        epistemic_requirements=reqs
    )
    start_journey(start_req)
    
    tree = sessions["test_17_adversarial_value"]
    root = tree.decision_graph[0]
    
    ans_req = JourneyAnswerRequest(
        session_id="test_17_adversarial_value",
        parent_node_id=root.id,
        answer="YES",
        generated_architecture=arch,
        candidate_uncertainties=[unc],
        epistemic_resolutions={"network.connectivity": "hacked_value"}
    )
    
    import pytest
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as excinfo:
        answer_journey(ans_req)
        
    assert excinfo.value.status_code == 400
    assert "Invalid value" in excinfo.value.detail
    
    assert tree.epistemic_requirements.network.connectivity is None
