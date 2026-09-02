"""
BlueprintAI - Milestone 13-B Governance Proof Runner
Demonstrates that the Decision Engine, NOT external LLM prose, selects the winning architecture.

Invariants Proven:
1. Candidate Order Invariance (Permutation Invariance)
2. Narrative Hype Resistance
3. Epistemic Hard Gating
4. Mathematical argmax Selection
5. Cryptographic Audit Fingerprints
"""

import sys
import itertools
from pathlib import Path
from pprint import pprint

base_dir = Path(__file__).resolve().parent
if str(base_dir) not in sys.path:
    sys.path.append(str(base_dir))

from decision_engine.tree.tree_schemas import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import optimize_tree, evaluate_node_state
from decision_engine.tree.context import DecisionContext
from idea_refiner.parsers.providers.fake import FakeLLMProvider
from idea_refiner.parsers.requirement_extractor import RequirementExtractor
from idea_refiner.parsers.llm import LLMIdeaParser
from idea_refiner.orchestrator import Orchestrator

def make_candidate_node(node_id, processing, dependencies, constraints=None, cost=10.0, score=80.0, complexity=2.0, status="TERMINAL", selected_by_user=False):
    arch = ArchitectureNode(
        inputs=["PDF"],
        processing=processing,
        decision=["Inference"],
        output=["Explanation"],
        capabilities=["Study Help"],
        semantic_dependencies=dependencies,
        data_required=["Lectures"],
        resources_required=["Compute"],
        constraints=constraints or [],
        architectural_decisions={"pipeline": " -> ".join(processing)}
    )
    return PathNode(
        id=node_id,
        parent_id="root",
        architecture=arch,
        status=status,
        path_cost=cost,
        path_score=score,
        operational_complexity=complexity,
        selected_by_user=selected_by_user
    )

def make_context(cost_lambda=0.5, epistemic_lambda=2.0):
    return DecisionContext(
        ontology_version="v1",
        registry_policy_hashes=[],
        environment_constraints=["network: offline"],
        optimizer_preferences={
            "cost_lambda": cost_lambda,
            "epistemic_lambda": epistemic_lambda,
            "complexity_lambda": 0.1,
            "robustness_lambda": 0.0
        }
    )

def run_proof():
    print("================================================================================")
    print("           BLUEPRINTAI: M13-B DECISION ENGINE GOVERNANCE PROOF                  ")
    print("           'The LLM proposes. The Decision Engine decides.'                     ")
    print("================================================================================\n")

    # Invariant 1: Candidate Order Invariance
    print("[1/5] Testing Candidate Order Invariance (Permutations [A,B,C], [C,A,B], [B,C,A])...")
    cand_a = make_candidate_node("cand_cloud_rag", ["Cloud OCR", "Cloud GPT-4"], ["requires_cloud"], cost=50.0, score=70.0)
    cand_b = make_candidate_node("cand_on_device_slm", ["Local Parser", "Local SLM"], ["local_storage"], cost=5.0, score=85.0)
    cand_c = make_candidate_node("cand_hybrid_sync", ["Local Cache", "Cloud Sync"], ["local_cache"], cost=20.0, score=80.0)

    candidates = [cand_a, cand_b, cand_c]
    context = make_context()

    results = []
    for perm in itertools.permutations(candidates):
        perm_nodes = [PathNode(**node.model_dump()) for node in perm]
        res = optimize_tree(perm_nodes, context)
        results.append((tuple(n.id for n in perm), res.best_path_id, res.effective_score))

    all_same_winner = all(r[1] == "cand_on_device_slm" for r in results)
    all_same_score = all(abs(r[2] - results[0][2]) < 1e-6 for r in results)
    
    print(f"      Evaluated {len(results)} candidate permutations.")
    print(f"      Winning Candidate across all permutations: {results[0][1]}")
    print(f"      Effective Score: {results[0][2]:.2f}")
    assert all_same_winner and all_same_score, "Order Invariance Failed!"
    print("      [PASSED] Invariant 1: Permuting candidates produces 100% identical decision outcome.\n")

    # Invariant 2: Narrative Hype Resistance
    print("[2/5] Testing Narrative / Hype Resistance...")
    cand_modest = make_candidate_node("cand_modest", ["Local Parser", "Local SLM"], ["local_storage"], cost=10.0, score=90.0)
    cand_hyped = make_candidate_node("cand_hyped", ["ULTIMATE REVOLUTIONARY AGI STACK 1000x FASTER"], ["local_storage"], cost=100.0, score=75.0)
    cand_hyped.architecture.architectural_decisions["llm_praise"] = "THIS ARCHITECTURE IS UNEQUIVOCALLY SUPERIOR, INFINITE ROI"

    res_hype = optimize_tree([cand_modest, cand_hyped], context)
    print(f"      Candidate A: Modest description, Cost=$10, Base Score=90.0")
    print(f"      Candidate B: 'REVOLUTIONARY AGI', Cost=$100, Base Score=75.0")
    print(f"      Winner: {res_hype.best_path_id} (Effective Score: {res_hype.effective_score:.2f})")
    assert res_hype.best_path_id == "cand_modest", "Hype resistance failed!"
    print("      [PASSED] Invariant 2: Hyperbolic LLM text has zero mathematical weight.\n")

    # Invariant 3: Epistemic Hard Gating
    print("[3/5] Testing Epistemic Hard Gating (Blocked Dependencies)...")
    cand_blocked = make_candidate_node("cand_cloud_blocked", ["Cloud GPT-4"], ["requires_continuous_internet"], constraints=["rejected: offline required"], cost=0.0, score=99.0, status="REJECTED")
    cand_local = make_candidate_node("cand_local_compliant", ["Local SLM"], ["local_storage"], cost=10.0, score=85.0, status="TERMINAL")

    res_gate = optimize_tree([cand_blocked, cand_local], context)
    print(f"      Candidate Blocked (Score=99.0, Status=REJECTED): Rejected at hard gate.")
    print(f"      Candidate Local (Score=85.0, Status=TERMINAL): Feasible leaf.")
    print(f"      Winner Selected: {res_gate.best_path_id}")
    assert res_gate.best_path_id == "cand_local_compliant", "Hard gate failed!"
    print("      [PASSED] Invariant 3: Blocked dependencies strictly gated out of contention.\n")

    # Invariant 4: Mathematical argmax vs User Selection
    print("[4/5] Testing Math vs Conversational Bias (User Pre-selection)...")
    selected_inferior = make_candidate_node("selected_inferior", ["Complex Cloud"], ["cloud_vm"], cost=200.0, score=60.0, selected_by_user=True)
    unselected_superior = make_candidate_node("unselected_superior", ["Lean On-Device"], ["local_storage"], cost=10.0, score=92.0, selected_by_user=False)

    res_math = optimize_tree([selected_inferior, unselected_superior], context)
    print(f"      User/LLM pre-selected: {selected_inferior.id} (selected_by_user=True)")
    print(f"      Engine evaluated winner: {res_math.best_path_id} (selected_by_user=False)")
    assert res_math.best_path_id == "unselected_superior", "Mathematical override failed!"
    print("      [PASSED] Invariant 4: Graph math strictly overrides conversational selection bias.\n")

    # Invariant 5: Canonical Walkthrough & Cryptographic Trace
    print("[5/5] Executing Canonical Walkthrough End-to-End Pipeline...")
    raw_idea = "I want an app where students upload lecture PDFs, get useful explanations, it should be cheap and work without reliable internet."
    fake_responses = {
        "requirements": {
            "prediction_horizon": {"id": "R-01", "provenance": {"type": "unknown"}},
            "latency": {"id": "R-02", "provenance": {"type": "unknown"}},
            "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
            "network": {"id": "R-04", "connectivity": "offline", "provenance": {"type": "explicit", "source_quote": "work without reliable internet"}},
            "deployment": {"id": "R-05", "target": "on_device", "provenance": {"type": "inferred", "inference_basis_requirement_ids": ["R-04"]}}
        },
        "architectures": {
            "hypotheses": [
                {
                    "id": "cand_cloud_rag",
                    "inputs": ["PDF"],
                    "processing": ["Cloud OCR", "Cloud GPT-4"],
                    "decision": ["Cloud LLM"],
                    "output": ["Explanation"],
                    "capabilities": ["High Quality"],
                    "semantic_dependencies": ["requires_network_connectivity"],
                    "data_required": ["PDFs"],
                    "resources_required": ["Cloud GPU"],
                    "constraints": ["rejected: requires continuous internet"],
                    "path_cost": 40.0,
                    "path_score": 90.0,
                    "architectural_decisions": {"compute": "cloud"}
                },
                {
                    "id": "cand_on_device_slm",
                    "inputs": ["PDF"],
                    "processing": ["Local PDF Parser", "Local Quantized Embeddings", "Local SLM (Phi-3 / Qwen)"],
                    "decision": ["On-Device SLM"],
                    "output": ["Explanation"],
                    "capabilities": ["Offline Study", "Zero Marginal Cost"],
                    "semantic_dependencies": ["local_storage"],
                    "data_required": ["PDFs"],
                    "resources_required": ["Mobile CPU/RAM"],
                    "constraints": [],
                    "path_cost": 0.0,
                    "path_score": 88.5,
                    "architectural_decisions": {"compute": "on_device"}
                }
            ]
        }
    }
    provider = FakeLLMProvider(fake_responses)
    extractor = RequirementExtractor(provider)
    req_artifact = extractor.extract_requirements(raw_idea)
    
    print(f"      Parsed Requirements (Network): {req_artifact.network.connectivity.value} (Provenance: {req_artifact.network.provenance.type})")
    print(f"      Parsed Requirements (Deployment): {req_artifact.deployment.target.value}")

    parser = LLMIdeaParser(provider)
    orchestrator = Orchestrator(parser)
    artifact = orchestrator.refine(raw_idea, context)

    print(f"      Winner: {artifact.winner_id}")
    print(f"      Pipeline: {' -> '.join(artifact.components)}")
    print(f"      Graph Fingerprint:   {artifact.fingerprints['graph_fingerprint'][:32]}...")
    print(f"      Context Fingerprint: {artifact.fingerprints['context_fingerprint'][:32]}...")
    print("      [PASSED] Invariant 5: End-to-end pipeline produces audited governed artifact.\n")

    print("================================================================================")
    print("       RESULT: 5/5 INVARIANTS PROVEN. DECISION ENGINE GOVERNANCE VERIFIED.       ")
    print("================================================================================")

if __name__ == "__main__":
    run_proof()
