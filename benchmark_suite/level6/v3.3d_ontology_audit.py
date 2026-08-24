import sys
import os

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement
from decision_engine.input_layer.ontology import evaluate_ontology, infer_properties

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
    print("--- V3.3-D Ontology Audit Suite ---")
    
    # 1. Recognized dependency + applicable rule
    print("\nTest 1: Recognized + applicable policy (Deterministic consequence)")
    arch1 = make_arch(["requires_manual_usb_transfer"])
    res1 = evaluate_ontology(arch1, [], [make_req("Predict waiting time")])
    assert "Predict waiting time" in res1.requirement_failures
    print("PASS")

    # 2. Recognized dependency + no applicable policy
    print("\nTest 2: Recognized + no applicable policy (Informational)")
    arch2 = make_arch(["requires_heavy_anonymization"])
    # No "real_time_processing_required" constraint is present, so it shouldn't fail.
    res2 = evaluate_ontology(arch2, ["no_cloud_infrastructure"], [])
    assert len(res2.constraint_failures) == 0
    print("PASS")

    # 3. Safe property
    print("\nTest 3: Safe property (PASS)")
    # A dependency that doesn't trigger the failure condition (simulated by missing constraint/req)
    res3 = evaluate_ontology(make_arch(["test_recognized_triggering"]), ["no_cloud"], [make_req("Other Req")])
    assert len(res3.requirement_failures) == 0
    print("PASS")

    # 4. Exact threshold (Explicitly defined boundary)
    # We define a boundary rule: if "budget_less_than_500_per_month" constraint is present, manual_intensive fails it.
    print("\nTest 4: Exact threshold boundary")
    arch4 = make_arch(["requires_complex_scraping_or_manual_entry"])
    res4_just_under = evaluate_ontology(arch4, ["budget_less_than_1000"], [])
    assert len(res4_just_under.constraint_failures) == 0
    print("PASS: Just under threshold (no fail)")

    # 5. Just beyond threshold (FAIL)
    print("\nTest 5: Just beyond threshold (FAIL)")
    res4_over = evaluate_ontology(arch4, ["budget_less_than_500_per_month"], [])
    assert "budget_less_than_500_per_month_violated_by_complex_scraping" in res4_over.constraint_failures
    print("PASS")

    # 6. Unknown dependency
    print("\nTest 6: Unknown dependency (INFORMATIONAL)")
    arch6 = make_arch(["requires_magic_wand_processing"])
    props6 = infer_properties(["requires_magic_wand_processing"])
    res6 = evaluate_ontology(arch6, ["budget_less_than_500_per_month"], [make_req("Predict waiting time")])
    assert len(props6) == 0
    assert len(res6.requirement_failures) == 0 and len(res6.constraint_failures) == 0
    print("PASS")

    # 7. Recognized + unknown dependency
    print("\nTest 7: Recognized + unknown dependency (Only recognized has effect)")
    arch7 = make_arch(["requires_manual_usb_transfer", "requires_magic_wand_processing"])
    res7 = evaluate_ontology(arch7, [], [make_req("Predict waiting time")])
    assert "Predict waiting time" in res7.requirement_failures
    assert len(res7.constraint_failures) == 0
    print("PASS")

    # 8. Conflicting recognized rules
    print("\nTest 8: Conflicting recognized rules (Deterministic resolution)")
    arch8 = make_arch(["test_conflict_1", "test_conflict_2"])
    res8 = evaluate_ontology(arch8, [], [])
    assert "test_conflict_1_failure" in res8.constraint_failures
    assert "test_conflict_2_failure" in res8.constraint_failures
    print("PASS")

    # 9. Multiple recognized dependencies
    print("\nTest 9: Multiple recognized dependencies (Effects compose predictably)")
    arch9 = make_arch(["requires_manual_usb_transfer", "requires_complex_scraping_or_manual_entry"])
    res9 = evaluate_ontology(arch9, ["budget_less_than_500_per_month"], [make_req("Predict waiting time")])
    assert "Predict waiting time" in res9.requirement_failures
    assert "budget_less_than_500_per_month_violated_by_complex_scraping" in res9.constraint_failures
    print("PASS")

    print("\nAll Ontology Audit Tests PASSED.")

if __name__ == "__main__":
    run_tests()
