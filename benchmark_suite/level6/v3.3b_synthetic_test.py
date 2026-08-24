import sys
import os
import json

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement
from decision_engine.input_layer.ontology import evaluate_ontology, OntologyResult

def make_arch(deps) -> ArchitectureNode:
    return ArchitectureNode(
        inputs=[], processing=[], decision=[], output=[], capabilities=[],
        data_required=[], resources_required=[], constraints=[],
        evidence_provenance=[], historical_decisions=[],
        semantic_dependencies=deps, architectural_decisions={}
    )

def make_req(name) -> Requirement:
    return Requirement(name=name, required=True)

def run_tests():
    print("--- V3.3-B Synthetic Ontology Tests ---")
    
    # Test 1: recognized dependency + triggering condition
    print("\nTest 1: Recognized + Triggering")
    arch1 = make_arch(["requires_manual_usb_transfer"])
    reqs1 = [make_req("Predict Wait Times")]
    res1 = evaluate_ontology(arch1, [], reqs1)
    print(f"Req Failures: {res1.requirement_failures}")
    assert "Predict Wait Times" in res1.requirement_failures
    print("PASS")
    
    # Test 2: recognized dependency + non-triggering condition
    print("\nTest 2: Recognized + Non-triggering")
    arch2 = make_arch(["requires_heavy_anonymization"])
    # "30_day_prototype" is missing from env constraints
    res2 = evaluate_ontology(arch2, ["no_cloud_infrastructure"], [])
    print(f"Constraint Failures: {res2.constraint_failures}")
    assert len(res2.constraint_failures) == 0
    print("PASS")
    
    # Test 3: unknown dependency
    print("\nTest 3: Unknown dependency")
    arch3 = make_arch(["requires_magic_wand_processing"])
    res3 = evaluate_ontology(arch3, ["no_cloud_infrastructure"], reqs1)
    print(f"Req Failures: {res3.requirement_failures}, Constraint Failures: {res3.constraint_failures}")
    assert len(res3.requirement_failures) == 0 and len(res3.constraint_failures) == 0
    print("PASS")
    
    # Test 4: multiple recognized dependencies
    print("\nTest 4: Multiple recognized dependencies")
    arch4 = make_arch(["requires_manual_usb_transfer", "requires_complex_scraping_or_manual_entry"])
    res4 = evaluate_ontology(arch4, ["budget_less_than_500_per_month"], reqs1)
    print(f"Req Failures: {res4.requirement_failures}, Constraint Failures: {res4.constraint_failures}")
    assert "Predict Wait Times" in res4.requirement_failures
    assert "budget_less_than_500_per_month_violated_by_complex_scraping" in res4.constraint_failures
    print("PASS")
    
    # Test 5: conflicting dependencies
    print("\nTest 5: Conflicting dependencies")
    # For now our rule just unions failures, so if one says fail A, another says fail B, both fail.
    arch5 = make_arch(["test_conflict_1", "test_conflict_2"])
    res5 = evaluate_ontology(arch5, [], [])
    print(f"Constraint Failures: {res5.constraint_failures}")
    assert "test_conflict_1_failure" in res5.constraint_failures
    assert "test_conflict_2_failure" in res5.constraint_failures
    print("PASS")
    
    print("\nAll Synthetic Ontology Tests PASSED.")

if __name__ == "__main__":
    run_tests()
