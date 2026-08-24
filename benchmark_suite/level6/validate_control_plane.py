import sys
import time
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from benchmark_suite.level6.control_plane.test_qualification import (
    test_gate1_stale_isolation_and_valid_dispatch,
    test_gate2_single_invocation_bounded_execution,
    test_gate3_end_to_end_full_identity_matching,
    test_gate4_failure_containment_and_hung_process_kill,
)

def run_qualification_suite():
    print("================================================================================")
    print("       PILOT 03 CONTROL-PLANE QUALIFICATION & VALIDATION SUITE                  ")
    print("================================================================================")
    print("Scientific Requirement: Prove control-plane integrity prior to Pilot 03 launch.")
    print("--------------------------------------------------------------------------------")

    gates = [
        ("Gate 1: Stale Isolation + Valid Dispatch", test_gate1_stale_isolation_and_valid_dispatch),
        ("Gate 2: Bounded Process Execution", test_gate2_single_invocation_bounded_execution),
        ("Gate 3: 5-D Identity Handshake & Schema Validation", test_gate3_end_to_end_full_identity_matching),
        ("Gate 4: Failure Containment & Hung Process Kill", test_gate4_failure_containment_and_hung_process_kill),
    ]

    all_passed = True
    for name, test_fn in gates:
        print(f"\n[RUNNING] {name}...")
        try:
            test_fn()
            print(f"[RESULT]  >>> {name}: PASS <<<")
        except Exception as e:
            all_passed = False
            print(f"[RESULT]  >>> {name}: FAIL <<<")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n================================================================================")
    if all_passed:
        print(" QUALIFICATION STATUS: 100% PASSED (ALL 4 GATES VERIFIED)")
        print(" Control plane is certified for bounded, authenticated Pilot 03 execution.")
    else:
        print(" QUALIFICATION STATUS: FAILED")
        print(" Do NOT proceed to Pilot 03 until all qualification failures are resolved.")
    print("================================================================================")
    
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_qualification_suite()
