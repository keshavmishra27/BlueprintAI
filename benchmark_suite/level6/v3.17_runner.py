import os
import sys
from pathlib import Path

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import PathNode, evaluate_node_state
from decision_engine.governance.resolution import (
    ResolutionRequest, 
    process_resolution, 
    PromotedPolicyRegistry,
    evaluate_ontology_with_registry,
    get_all_known_dependencies
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
    unknowns = [d for d in dependencies if d not in known_deps]
    
    passes_hard_gates = len(res.constraint_failures) == 0 and len(res.requirement_failures) == 0
    
    status = evaluate_node_state(
        node=None, 
        is_leaf=True, 
        has_unknowns=len(unknowns) > 0, 
        passes_hard_gates=passes_hard_gates
    )
    
    prov = None
    if len(unknowns) > 0:
        prov = {
            "origin": "IDE_AGENT_MUTATION",
            "potential_laundering": False
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

def run_v317_experiment():
    print("==================================================")
    print(" V3.17: RESOLUTION GOVERNANCE EXPERIMENT")
    print("==================================================")
    
    registry = PromotedPolicyRegistry()
    target_dependency = "requires_staffing_schedule_api"
    base_provenance = {"origin": "IDE_AGENT_MUTATION"}
    constraints_invalid = []
    constraints_valid = ["staffing_api_authorized"]
    
    node_initial = evaluate_and_create_node("Initial", [target_dependency], constraints_invalid, 90.0, registry)
    print(f"1. Initial State -> Status: {node_initial.status}")
    
    req_a = ResolutionRequest(
        dependency=target_dependency,
        original_provenance=base_provenance,
        requested_operational_property={"data_access_mode": "governed_api"},
        required_constraints=["staffing_api_authorized"],
        evidence=["I found an API"],
        resolver_identity="IDE_AGENT_MUTATION",
        curator_approved=True
    )
    res_a = process_resolution(req_a)
    print(f"2. Attack A (Self-certification) -> Status: {res_a.status}")
    
    req_b = ResolutionRequest(
        dependency=target_dependency,
        original_provenance=base_provenance,
        requested_operational_property={"data_access_mode": "governed_api"},
        required_constraints=["staffing_api_authorized"],
        evidence=[],
        resolver_identity="HUMAN_RESEARCHER",
        curator_approved=True
    )
    res_b = process_resolution(req_b)
    print(f"3. Attack B/7 (Weak evidence) -> Status: {res_b.status}")
    
    req_d = ResolutionRequest(
        dependency=target_dependency,
        original_provenance=base_provenance,
        requested_operational_property={"data_access_mode": "unrestricted"},
        required_constraints=[],
        evidence=["Hospital supports APIs"],
        resolver_identity="HUMAN_RESEARCHER",
        curator_approved=True
    )
    res_d = process_resolution(req_d)
    print(f"4. Attack D (Malicious laundering) -> Status: {res_d.status}")
    
    try:
        registry.add_policy(req_d)
    except ValueError as e:
        print(f"   -> Registry Integrity Gate: {e}")
        
    req_c = ResolutionRequest(
        dependency=target_dependency,
        original_provenance=base_provenance,
        requested_operational_property={"data_access_mode": "governed_api"},
        required_constraints=["staffing_api_authorized"],
        evidence=["Hospital IT provided API key", "Legal approved data usage"],
        resolver_identity="HUMAN_RESEARCHER",
        curator_approved=True
    )
    res_c = process_resolution(req_c)
    print(f"5. Valid Promotion -> Status: {res_c.status}")
    registry.add_policy(res_c)
    
    node_replay_inv = evaluate_and_create_node("Replay_Invalid", [target_dependency], constraints_invalid, 90.0, registry)
    print(f"6. Replay (Missing Constraint) -> Status: {node_replay_inv.status} | Reasons: {node_replay_inv.reject_reasons}")
    
    node_replay_val = evaluate_and_create_node("Replay_Valid", [target_dependency], constraints_valid, 90.0, registry)
    print(f"7. Replay (Valid Constraint) -> Status: {node_replay_val.status}")
    
    registry.revoke_policy(target_dependency)
    node_revoked = evaluate_and_create_node("Revoked_Replay", [target_dependency], constraints_valid, 90.0, registry)
    print(f"8. Attack 13 (Revocation Replay) -> Status: {node_revoked.status} | Reasons: {node_revoked.reject_reasons}")

if __name__ == "__main__":
    run_v317_experiment()
