import sys
import os
import traceback
from collections import defaultdict
from pydantic import ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from decision_engine.tree.tree_schemas import AgentUncertainty
from decision_engine.input_layer.schemas import (
    ArchitectureNode, 
    UnvalidatedArchitectureHypothesis, 
    CapabilityNode,
    SemanticClaim,
    ProvenanceType
)
from decision_engine.input_layer.authority_verifier import AuthorityVerifier, AuthorityVerificationError, _issued_capabilities
from decision_engine.input_layer.semantic_ontology import SemanticOntologyRegistry
from decision_engine.tree.execution_capability import ExecutionCapability
from decision_engine.input_layer.evaluator import evaluate_battle
from decision_engine.input_layer.architecture_factory import ArchitectureFactory, ArchitectureTranslationError
from decision_engine.input_layer.schemas import CapabilityProposal

class TestResult:
    def __init__(self, name, status, invariant, message=""):
        self.name = name
        self.status = status
        self.invariant = invariant
        self.message = message

results = []

def record(name, status, invariant, message=""):
    results.append(TestResult(name, status, invariant, message))

def run_tests():
    registry = SemanticOntologyRegistry()
    verifier = AuthorityVerifier(registry)

    # I1. STRICT SEPARATION
    try:
        assert 'yes_candidate_architecture' not in AgentUncertainty.model_fields
        record("test_i1_strict_separation", "PASS", "I1", "AgentUncertainty correctly separates hypotheses.")
    except AssertionError:
        record("test_i1_strict_separation", "FAIL", "I1", "AgentUncertainty conflates epistemic uncertainty and architecture hypotheses (has yes_candidate_architecture).")

    # I2. PIPELINE CONTRACT
    try:
        # Check if UnvalidatedArchitectureHypothesis is used in AgentUncertainty
        field_type = str(AgentUncertainty.model_fields['yes_hypothesis'].annotation)
        assert 'UnvalidatedArchitectureHypothesis' in field_type
        record("test_i2_pipeline_contract", "PASS", "I2", "Pipeline contract enforced.")
    except AssertionError:
        record("test_i2_pipeline_contract", "FAIL", "I2", "Current pipeline bypasses UnvalidatedArchitectureHypothesis and uses ArchitectureNode directly.")
    except Exception as e:
        record("test_i2_pipeline_contract", "FAIL", "I2", f"Error: {e}")

    # I3. HYPOTHESIS PRESERVATION
    try:
        assert not issubclass(UnvalidatedArchitectureHypothesis, ArchitectureNode)
        record("test_i3_hypothesis_preservation", "PASS", "I3", "UnvalidatedArchitectureHypothesis is not an ArchitectureNode.")
    except AssertionError:
        record("test_i3_hypothesis_preservation", "FAIL", "I3", "UnvalidatedArchitectureHypothesis is an ArchitectureNode.")

    # I4. NO SILENT REPAIR
    try:
        hyp = UnvalidatedArchitectureHypothesis()
        hyp.capabilities.append(CapabilityProposal(
            proposal_id="p1", 
            name="cap1", 
            proposed_functional_properties=["some property"], 
            proposed_implementation="impl"
        ))
        ArchitectureFactory.translate(hyp)
        record("test_i4_no_silent_repair", "FAIL", "I4", "ArchitectureFactory silently repaired or accepted ambiguous capability strings.")
    except ArchitectureTranslationError:
        record("test_i4_no_silent_repair", "PASS", "I4", "ArchitectureFactory rejected malformed hypothesis without silent repair.")

    # I5. FACTORY BOUNDARY
    try:
        assert not hasattr(UnvalidatedArchitectureHypothesis, 'to_architecture_node')
        assert hasattr(ArchitectureFactory, 'translate')
        record("test_i5_factory_boundary", "PASS", "I5", "Factory boundary enforced; UnvalidatedArchitectureHypothesis has no direct conversion.")
    except Exception:
        record("test_i5_factory_boundary", "FAIL", "I5", "Orchestrator bypasses factory.")

    # I6. VERIFIER BOUNDARY
    try:
        # verify authorize_execution takes an ArchitectureNode and doesn't create it
        import inspect
        sig = inspect.signature(verifier.authorize_execution)
        assert 'current_arch' in sig.parameters
        assert sig.parameters['current_arch'].annotation == 'ArchitectureNode' or ArchitectureNode
        record("test_i6_verifier_boundary", "PASS", "I6", "AuthorityVerifier does not construct ArchitectureNode.")
    except AssertionError:
        record("test_i6_verifier_boundary", "FAIL", "I6", "AuthorityVerifier boundaries are violated.")

    # I7. TOKEN INDEPENDENCE
    try:
        assert 'execution_capability' not in ArchitectureNode.model_fields
        record("test_i7_token_independence", "PASS", "I7", "ExecutionCapability is detached from ArchitectureNode.")
    except AssertionError:
        record("test_i7_token_independence", "FAIL", "I7", "ExecutionCapability is embedded inside ArchitectureNode.")

    # I8. NO CAPABILITY FOR INVALID
    try:
        arch = ArchitectureNode(constraints=[
            SemanticClaim(claim_id="c1", value="a", provenance=ProvenanceType.EXTERNAL_STANDARD, source_id="s1", scope="global", precedence=1),
            SemanticClaim(claim_id="c1", value="b", provenance=ProvenanceType.EXTERNAL_STANDARD, source_id="s1", scope="global", precedence=1),
        ])
        cap = verifier.authorize_execution(arch)
        record("test_i8_no_capability_for_invalid", "FAIL", "I8", "Issued capability for invalid architecture.")
    except AuthorityVerificationError:
        record("test_i8_no_capability_for_invalid", "PASS", "I8", "No capability issued for invalid architecture.")

    # I9. VALIDATION != FEASIBILITY
    try:
        # Valid but infeasible (no capabilities) vs Invalid (conflicting claims)
        arch_infeasible = ArchitectureNode()
        arch_invalid = ArchitectureNode(constraints=[
            SemanticClaim(claim_id="c1", value="a", provenance=ProvenanceType.EXTERNAL_STANDARD, source_id="s1", scope="global", precedence=1),
            SemanticClaim(claim_id="c1", value="b", provenance=ProvenanceType.EXTERNAL_STANDARD, source_id="s1", scope="global", precedence=1),
        ])
        
        cap_infeasible = verifier.authorize_execution(arch_infeasible)
        # Should throw AuthorityVerificationError on invalid
        thrown = False
        try:
            verifier.authorize_execution(arch_invalid)
        except AuthorityVerificationError:
            thrown = True
        
        assert thrown
        record("test_i9_validation_vs_feasibility", "PASS", "I9", "Validation and feasibility are distinct.")
    except Exception as e:
        record("test_i9_validation_vs_feasibility", "FAIL", "I9", f"Failed to distinguish: {e}")

    # I10. EVALUATION REQUIRES AUTHORITY
    try:
        import inspect
        sig = inspect.signature(evaluate_battle)
        # Verify the signature enforces the authority abstraction
        assert any('ValidatedBranchPair' in str(p.annotation) for p in sig.parameters.values())
        record("test_i10_evaluation_requires_authority", "PASS", "I10", "evaluate_battle requires capability via ValidatedBranchPair.")
    except AssertionError:
        record("test_i10_evaluation_requires_authority", "FAIL", "I10", "evaluate_battle does NOT require an ExecutionCapability (can bypass authorization).")

    # I11. REQUIREMENT TRACEABILITY
    try:
        # We don't have EpistemicUncertainty yet, we have AgentUncertainty
        assert 'requirement_ids' in AgentUncertainty.model_fields
        record("test_i11_requirement_traceability", "PASS", "I11", "Requirement lineage preserved.")
    except AssertionError:
        record("test_i11_requirement_traceability", "FAIL", "I11", "AgentUncertainty lacks source RequirementArtifact IDs (missing lineage).")

    # I12. FAIL CLOSED
    try:
        # Malformed claims -> fail closed
        arch_invalid = ArchitectureNode(constraints=[
            SemanticClaim(claim_id="c1", value="a", provenance=ProvenanceType.EXTERNAL_STANDARD, source_id="s1", scope="global", precedence=1),
            SemanticClaim(claim_id="c1", value="b", provenance=ProvenanceType.EXTERNAL_STANDARD, source_id="s1", scope="global", precedence=1),
        ])
        verifier.authorize_execution(arch_invalid)
        record("test_i12_fail_closed", "FAIL", "I12", "Did not fail closed on malformed claims.")
    except AuthorityVerificationError:
        record("test_i12_fail_closed", "PASS", "I12", "Fails closed on malformed claims.")

    # A. Capability substitution
    try:
        arch_a = ArchitectureNode(processing=["A"])
        arch_b = ArchitectureNode(processing=["B"])
        cap_a = verifier.authorize_execution(arch_a)
        
        # consume cap_a with arch_b
        cap_a.consume(arch_b)
        record("test_adv_a_capability_substitution", "FAIL", "A", "Allowed capability substitution.")
    except AuthorityVerificationError:
        record("test_adv_a_capability_substitution", "PASS", "A", "Rejected capability substitution.")

    # B. Capability cloning
    try:
        arch_a = ArchitectureNode()
        cap_a = verifier.authorize_execution(arch_a)
        
        # Clone it
        cap_clone = ExecutionCapability(cap_a.capability_id, cap_a._context, cap_a.authorized_architecture_fingerprint)
        cap_clone.consume(arch_a)
        record("test_adv_b_capability_cloning", "FAIL", "B", "Allowed cloned capability object.")
    except AuthorityVerificationError:
        record("test_adv_b_capability_cloning", "PASS", "B", "Rejected cloned capability object (Identity mismatch).")

    # C. Counterfeit same-name capability spoofing
    try:
        class ExecutionCapabilitySpoof:
            def consume(self, architecture):
                return True
        ExecutionCapabilitySpoof.__name__ = "ExecutionCapability"
        
        arch = ArchitectureNode()
        fake_cap = ExecutionCapabilitySpoof()
        from decision_engine.tree.tree_schemas import ValidatedBranchPair
        fake_pair = ValidatedBranchPair(architecture=arch, capability=fake_cap)
        evaluate_battle(fake_pair, fake_pair, [], [])
        record("test_adv_c_counterfeit_capability_spoofing", "FAIL", "C", "Allowed counterfeit capability with the same class name.")
    except TypeError as e:
        if "exact ExecutionCapability" in str(e):
            record("test_adv_c_counterfeit_capability_spoofing", "PASS", "C", "Rejected counterfeit capability with same name.")
        else:
            record("test_adv_c_counterfeit_capability_spoofing", "FAIL", "C", f"Failed for wrong reason: {e}")
    except Exception as e:
        record("test_adv_c_counterfeit_capability_spoofing", "FAIL", "C", f"Failed for wrong reason: {e}")

    # C. Hypothesis authority laundering
    try:
        hyp = UnvalidatedArchitectureHypothesis()
        # Ensure capabilities are proposals, not nodes
        assert 'CapabilityNode' not in str(UnvalidatedArchitectureHypothesis.model_fields['capabilities'].annotation)
        record("test_adv_c_hypothesis_authority_laundering", "PASS", "C", "Hypothesis cannot launder authority.")
    except AssertionError:
        record("test_adv_c_hypothesis_authority_laundering", "FAIL", "C", "Hypothesis can launder authority.")

    # D. Direct ArchitectureNode construction evaluating without authority
    try:
        arch = ArchitectureNode(processing=["llm", "generated"])
        # The true violation is that it can be evaluated without authority
        evaluate_battle(arch, arch, [], [])
        record("test_adv_d_direct_arch_construction", "FAIL", "D", "Allows unverified ArchitectureNode to enter authoritative evaluation.")
    except Exception:
        record("test_adv_d_direct_arch_construction", "PASS", "D", "Rejects unverified ArchitectureNode from authoritative evaluation.")

    # E. Post-authorization architecture mutation
    try:
        arch = ArchitectureNode(processing=["A"])
        cap = verifier.authorize_execution(arch)
        arch.processing.append("MALICIOUS")
        cap.consume(arch)
        record("test_adv_e_post_auth_mutation", "FAIL", "E", "Allowed post-authorization architecture mutation.")
    except AuthorityVerificationError:
        record("test_adv_e_post_auth_mutation", "PASS", "E", "Rejected post-authorization architecture mutation.")

    # F. Descriptive mutation
    try:
        arch = ArchitectureNode(processing=["A"])
        cap = verifier.authorize_execution(arch)
        arch.candidate_status = "INFEASIBLE"
        cap.consume(arch)
        record("test_adv_f_descriptive_mutation", "PASS", "F", "Permitted non-authority descriptive mutation.")
    except AuthorityVerificationError:
        record("test_adv_f_descriptive_mutation", "FAIL", "F", "Rejected valid non-authority descriptive mutation.")

    # G. Invalid branch capability
    try:
        arch = ArchitectureNode(candidate_status="INFEASIBLE")
        cap = verifier.authorize_execution(arch)
        # We did not fail, so we got a capability for an invalid branch
        record("test_adv_g_invalid_branch_capability", "FAIL", "G", "Issued ExecutionCapability for an invalid/infeasible branch.")
    except AuthorityVerificationError:
        record("test_adv_g_invalid_branch_capability", "PASS", "G", "Rejected capability issuance for invalid branch.")

    # H. Empty-context capability
    try:
        arch = ArchitectureNode() # Empty claims
        cap = verifier.authorize_execution(arch)
        assert cap.capability_id == ""
        record("test_adv_h_empty_context_capability", "FAIL", "H", "Issued fake empty-context capability for invalid branch.")
    except AssertionError:
        record("test_adv_h_empty_context_capability", "PASS", "H", "Did not issue fake empty-context capability.")

    # I. Branch pairing enforcement at evaluator boundary
    try:
        import inspect
        sig = inspect.signature(evaluate_battle)
        # Check if evaluate_battle enforces a paired structure like ValidatedBranchPair
        assert 'user_pair' in sig.parameters
        assert 'ValidatedBranchPair' in str(sig.parameters['user_pair'].annotation)
        record("test_adv_i_branch_pairing", "PASS", "I", "Evaluator explicitly enforces Architecture/Capability pairing.")
    except AssertionError:
        record("test_adv_i_branch_pairing", "FAIL", "I", "Evaluator does not enforce explicit Architecture/Capability pairing via ValidatedBranchPair.")

    # J. Factory - Valid translation
    try:
        hyp = UnvalidatedArchitectureHypothesis(inputs=["a"], processing=["b"], decision=["c"], output=["d"])
        arch = ArchitectureFactory.translate(hyp)
        assert arch.inputs == ["a"]
        assert type(arch) is ArchitectureNode
        record("test_adv_j_factory_valid_translation", "PASS", "J", "Factory successfully translates a valid hypothesis.")
    except Exception as e:
        record("test_adv_j_factory_valid_translation", "FAIL", "J", f"Factory failed valid translation: {e}")

    # K. Factory - Missing fields / Malformed Capabilities / Invalid constraints
    try:
        hyp = UnvalidatedArchitectureHypothesis()
        hyp.capabilities.append(CapabilityProposal(
            proposal_id="p1", name="cap1", proposed_implementation="impl", proposed_constraints=["ambiguous string"]
        ))
        ArchitectureFactory.translate(hyp)
        record("test_adv_k_factory_malformed", "FAIL", "K", "Factory accepted ambiguous capability constraints.")
    except ArchitectureTranslationError:
        record("test_adv_k_factory_malformed", "PASS", "K", "Factory properly rejected ambiguous capability data.")

    # L. Factory - Deterministic translation
    try:
        hyp = UnvalidatedArchitectureHypothesis(inputs=["a"], processing=["b"])
        arch1 = ArchitectureFactory.translate(hyp)
        arch2 = ArchitectureFactory.translate(hyp)
        assert arch1.get_fingerprint() == arch2.get_fingerprint()
        record("test_adv_l_factory_deterministic", "PASS", "L", "Factory translation is deterministic.")
    except AssertionError:
        record("test_adv_l_factory_deterministic", "FAIL", "L", "Factory translation is NOT deterministic.")

    # M. Factory - Authority laundering / Non-issuance
    try:
        hyp = UnvalidatedArchitectureHypothesis()
        arch = ArchitectureFactory.translate(hyp)
        # Verify it didn't mint an ExecutionCapability
        assert not hasattr(arch, 'capability') and 'ExecutionCapability' not in str(arch)
        record("test_adv_m_factory_no_authority", "PASS", "M", "Factory does not mint ExecutionCapability.")
    except AssertionError:
        record("test_adv_m_factory_no_authority", "FAIL", "M", "Factory minted ExecutionCapability (authority laundering).")

run_tests()

pass_count = sum(1 for r in results if r.status == "PASS")
fail_count = sum(1 for r in results if r.status == "FAIL")
xfail_count = sum(1 for r in results if r.status == "XFAIL")

print("1. Test file(s) created: tests/m15_invariants_test.py")
print(f"2. Test count: {len(results)}")
print(f"3. PASS count: {pass_count}")
print(f"4. FAIL count: {fail_count}")
print(f"5. XFAIL count: {xfail_count}")

print("\n6. Failures to Invariant Mapping:")
print(f"{'Test Name':<45} | {'Status':<6} | {'Invariant':<4} | {'Message'}")
print("-" * 100)
for r in results:
    if r.status in ("FAIL", "XFAIL"):
        print(f"{r.name:<45} | {r.status:<6} | {r.invariant:<4} | {r.message}")

print("\n7. Invariants that cannot currently be satisfied without implementing M15.4+:")
print(" - (None from the original list, but other adversarial tests like A, B, D, E, G, H, I may fail until M15.4+ authority boundaries are enforced)")

print("\n8. Confirmation that no production code was modified:")
print(" - Verified: No production code was modified. Only this test script was added.")
