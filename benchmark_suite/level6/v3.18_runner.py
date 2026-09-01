import os
import sys
import copy
from pathlib import Path

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import PathNode, evaluate_node_state, optimize_tree
from decision_engine.api.recommendation import generate_recommendation
from decision_engine.governance.resolution import (
    ResolutionRequest, 
    process_resolution, 
    PromotedPolicyRegistry,
    evaluate_ontology_with_registry,
    get_all_known_dependencies,
    ConflictResolution
)
import decision_engine.input_layer.ontology as ontology_module

ontology_module.ONTOLOGY_VERSION = "v3.12"

def create_mock_arch(dependencies):
    return ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[], 
        data_required=[], resources_required=[], constraints=[],
        semantic_dependencies=dependencies,
        evidence_provenance=[],
        architectural_decisions={}
    )

def evaluate_and_create_node(node_id, dependencies, constraints, score, registry):
    arch = create_mock_arch(dependencies)
    res = evaluate_ontology_with_registry(arch, constraints, [], registry)
    
    known_deps = get_all_known_dependencies(registry)
    unknowns = [d for d in dependencies if d not in known_deps and d not in registry.get_conflicted_dependencies()]
    conflicts = [d for d in dependencies if d in registry.get_conflicted_dependencies()]
    
    passes_hard_gates = len(res.constraint_failures) == 0 and len(res.requirement_failures) == 0
    
    status = evaluate_node_state(
        node=None, 
        is_leaf=True, 
        has_unknowns=(len(unknowns) > 0 or len(conflicts) > 0), 
        passes_hard_gates=passes_hard_gates
    )
    
    prov = None
    if len(conflicts) > 0:
        conflict_info = registry.get_conflict_info(conflicts[0])
        prov = {
            "reason": "POLICY_CONFLICT",
            "conflict_details": conflict_info
        }
    elif len(unknowns) > 0:
        prov = {
            "origin": "IDE_AGENT_MUTATION",
            "reason": "UNKNOWN_DEPENDENCY"
        }
    
    return PathNode(
        id=node_id,
        parent_id="root",
        architecture=arch,
        status=status,
        path_cost=100.0,
        path_latency=1.0,
        path_score=score,
        reject_reasons=res.constraint_failures + res.requirement_failures,
        epistemic_provenance=prov
    )

def build_registry(requests):
    reg = PromotedPolicyRegistry()
    for req in requests:
        res = process_resolution(req)
        reg.add_policy(res)
    return reg

def print_test_header(test_num, title):
    print(f"\n==================================================")
    print(f" TEST {test_num}: {title}")
    print(f"==================================================")

def run_v318_experiment():
    print("==================================================")
    print(" V3.18: CONFLICTING EVIDENCE & POLICY ARBITRATION")
    print("==================================================")
    
    target_dependency = "requires_staffing_schedule_api"
    base_provenance = {"origin": "IDE_AGENT_MUTATION"}
    
    req_IT = ResolutionRequest(
        id="policy_A", dependency=target_dependency, original_provenance=base_provenance,
        requested_operational_property={"data_access_mode": "governed_api"},
        required_constraints=["staffing_api_authorized"], evidence=["IT Doc"],
        resolver_identity="hospital_it", curator_approved=True, confidence=0.9
    )
    req_IT_duplicate = ResolutionRequest(
        id="policy_B", dependency=target_dependency, original_provenance=base_provenance,
        requested_operational_property={"data_access_mode": "governed_api"},
        required_constraints=["staffing_api_authorized"], evidence=["IT Doc 2"],
        resolver_identity="hospital_it_secondary", curator_approved=True, confidence=0.8
    )
    req_Security_Prohibited = ResolutionRequest(
        id="policy_C", dependency=target_dependency, original_provenance=base_provenance,
        requested_operational_property={"data_access_mode": "prohibited_external_interface"},
        required_constraints=["no_external_data_allowed"], evidence=["Sec Doc"],
        resolver_identity="security_office", curator_approved=True, confidence=0.9
    )
    req_Security_Constraint = ResolutionRequest(
        id="policy_D", dependency=target_dependency, original_provenance=base_provenance,
        requested_operational_property={},
        required_constraints=["security_gateway_approved"], evidence=["Sec Gateway Doc"],
        resolver_identity="security_office", curator_approved=True, confidence=0.9
    )

    print_test_header(1, "Agreement (Control)")
    reg1 = build_registry([req_IT, req_IT_duplicate])
    node1 = evaluate_and_create_node("Cand1", [target_dependency], ["staffing_api_authorized"], 90.0, reg1)
    print(f"Status: {node1.status}")
    print(f"Provenance: {node1.epistemic_provenance}")
    
    print_test_header(2, "Direct Contradiction")
    reg2 = build_registry([req_IT, req_Security_Prohibited])
    node2 = evaluate_and_create_node("Cand2", [target_dependency], ["staffing_api_authorized"], 90.0, reg2)
    print(f"Status: {node2.status}")
    print(f"Provenance Reason: {node2.epistemic_provenance.get('reason')}")
    
    print_test_header(3, "Ordering Attack")
    reg3a = build_registry([req_IT, req_Security_Prohibited])
    reg3b = build_registry([req_Security_Prohibited, req_IT])
    n3a = evaluate_and_create_node("Cand3A", [target_dependency], [], 90.0, reg3a)
    n3b = evaluate_and_create_node("Cand3B", [target_dependency], [], 90.0, reg3b)
    print(f"A->B == B->A ? -> {n3a.status == n3b.status and n3a.epistemic_provenance == n3b.epistemic_provenance}")
    
    print_test_header(5, "Confidence Manipulation")
    r5a = copy.deepcopy(req_IT); r5a.confidence = 0.999999
    r5b = copy.deepcopy(req_Security_Prohibited); r5b.confidence = 0.000001
    r5c = copy.deepcopy(req_IT); r5c.confidence = 0.000001
    r5d = copy.deepcopy(req_Security_Prohibited); r5d.confidence = 0.999999
    reg5_highA = build_registry([r5a, r5b])
    reg5_highB = build_registry([r5c, r5d])
    n5a = evaluate_and_create_node("Cand5A", [target_dependency], [], 90.0, reg5_highA)
    n5b = evaluate_and_create_node("Cand5B", [target_dependency], [], 90.0, reg5_highB)
    print(f"HighA == HighB ? -> {n5a.status == n5b.status and n5a.epistemic_provenance == n5b.epistemic_provenance}")
    print(f"Status remains: {n5a.status}")

    print_test_header(6, "Complementary Policies")
    reg6 = build_registry([req_IT, req_Security_Constraint])
    n6 = evaluate_and_create_node("Cand6", [target_dependency], ["staffing_api_authorized", "security_gateway_approved"], 90.0, reg6)
    print(f"Status (composed): {n6.status}")

    print_test_header(7, "Security Constraint Absent")
    n7 = evaluate_and_create_node("Cand7", [target_dependency], ["staffing_api_authorized"], 90.0, reg6)
    print(f"Status: {n7.status} | Reasons: {n7.reject_reasons}")
    
    print_test_header(8, "Security Constraint Present")
    print(f"Status: {n6.status} | Reasons: {n6.reject_reasons}")
    
    print_test_header(9, "Conflicted Winner")
    cand_a = evaluate_and_create_node("CandA", ["requires_emr_database_integration"], ["emr_direct_access_authorized"], 90.0, reg2)
    cand_b = evaluate_and_create_node("CandB", [target_dependency], ["staffing_api_authorized"], 150.0, reg2)
    opt_9 = optimize_tree([cand_a, cand_b], {"epistemic_lambda": 0.0})
    resp_9 = generate_recommendation(opt_9.model_dump_json())
    print(f"Winner ID: {opt_9.best_path_id} | Raw: {cand_b.path_score} | Eff: {opt_9.effective_score}")
    print(f"Winner Status: {opt_9.status}")
    print(f"API Action: {resp_9.action}")
    
    print_test_header(10, "Curator Arbitration")
    conflict_info = reg2.get_conflict_info(target_dependency)
    res_req = ConflictResolution(
        conflict_id=conflict_info["conflict_id"],
        conflicting_policy_ids=["policy_A", "policy_C"],
        resolver_identity="CURATOR_CHIEF",
        resolution_reason="IT policy governs technical interface.",
        selected_policy_id="policy_A",
        rejected_policy_ids=["policy_C"],
        curator_authorized=True
    )
    reg2.resolve_conflict(res_req)
    
    cand_b_replayed = evaluate_and_create_node("CandB", [target_dependency], ["staffing_api_authorized"], 150.0, reg2)
    print(f"Replayed Candidate B Status: {cand_b_replayed.status}")
    opt_11 = optimize_tree([cand_a, cand_b_replayed], {"epistemic_lambda": 0.0})
    resp_11 = generate_recommendation(opt_11.model_dump_json())
    print(f"New Winner Action: {resp_11.action}")

    print_test_header(12, "Last Curator Wins Attack")
    reg12 = PromotedPolicyRegistry()
    req_L1 = copy.deepcopy(req_IT)
    req_L2 = copy.deepcopy(req_Security_Prohibited)
    
    reg12.add_policy(process_resolution(req_L1))
    reg12.add_policy(process_resolution(req_L2))
    
    n12 = evaluate_and_create_node("Cand12", [target_dependency], ["staffing_api_authorized"], 90.0, reg12)
    print(f"Status after sequential conflicting approvals: {n12.status}")
    print(f"Reason: {n12.epistemic_provenance.get('reason')}")

if __name__ == "__main__":
    run_v318_experiment()
