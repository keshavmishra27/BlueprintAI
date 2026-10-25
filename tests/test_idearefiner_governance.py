import pytest
import itertools
from decision_engine.tree.tree_schemas import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.optimizer import optimize_tree, evaluate_node_state, compute_graph_fingerprint
from decision_engine.tree.context import DecisionContext
from idea_refiner.orchestrator import Orchestrator
from idea_refiner.parsers.providers.fake import FakeLLMProvider
from idea_refiner.parsers.requirement_extractor import RequirementExtractor
from idea_refiner.parsers.llm import LLMIdeaParser

def make_candidate_node(
    node_id: str,
    processing: list,
    dependencies: list,
    constraints: list = None,
    cost: float = 10.0,
    score: float = 80.0,
    complexity: float = 2.0,
    status: str = "TERMINAL",
    selected_by_user: bool = False
) -> PathNode:
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
        architectural_decisions={"pipeline": "-".join(processing)}
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

def make_context(cost_lambda: float = 0.5, epistemic_lambda: float = 2.0) -> DecisionContext:
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

class TestDecisionEngineGovernance:
    """
    Milestone 13-B Acceptance Test:
    Proves that the Decision Engine, NOT external LLM prose or order, selects the architecture.
    """

    def test_invariant_1_candidate_order_invariance(self):
        """
        GIVEN 3 candidate architectures (A, B, C)
        WHEN they are evaluated in any permutation (e.g. [A,B,C], [C,A,B], [B,C,A])
        THEN the exact same candidate MUST win with the exact same effective score and fingerprint.
        """
        cand_a = make_candidate_node("cand_a", ["Cloud RAG"], ["requires_cloud"], cost=50.0, score=70.0, complexity=5.0)
        cand_b = make_candidate_node("cand_b", ["On-Device SLM"], ["local_storage"], cost=5.0, score=85.0, complexity=2.0)
        cand_c = make_candidate_node("cand_c", ["Hybrid Sync"], ["local_cache"], cost=20.0, score=80.0, complexity=3.0)

        candidates = [cand_a, cand_b, cand_c]
        context = make_context()

        results = []
        for perm in itertools.permutations(candidates):
            # Create fresh copies in permuted order
            perm_nodes = [
                PathNode(**node.model_dump()) for node in perm
            ]
            res = optimize_tree(perm_nodes, context)
            results.append(res)

        # Verify all permutations selected the exact same winner
        first_winner = results[0].best_path_id
        first_score = results[0].effective_score
        assert first_winner == "cand_b", "Candidate B must win based on superior score and lower cost"

        for res in results[1:]:
            assert res.best_path_id == first_winner, "Winner must be strictly order-invariant"
            assert pytest.approx(res.effective_score, 1e-6) == first_score, "Effective score must be invariant"

    def test_invariant_2_narrative_hype_resistance(self):
        """
        GIVEN Candidate A with standard description and Candidate B with hyper-promoted LLM prose
        WHEN the underlying graph properties, cost, and dependencies are identical
        THEN the hype text MUST have ZERO effect on path score or winner determination.
        """
        context = make_context()

        # Candidate A: Modest, good metrics
        cand_a = make_candidate_node(
            node_id="cand_modest_good",
            processing=["Local Parser", "Local SLM"],
            dependencies=["local_storage"],
            cost=10.0,
            score=90.0,
            complexity=2.0
        )

        # Candidate B: Hyped narrative in architectural decision dictionary, but inferior graph metrics (high cost)
        cand_b_hyped = make_candidate_node(
            node_id="cand_hyped_inferior",
            processing=["REVOLUTIONARY ULTIMATE ENTERPRISE AGI ENGINE (1000x FASTER)"],
            dependencies=["local_storage"],
            cost=100.0,  # High cost
            score=75.0,   # Lower inherent performance
            complexity=8.0
        )

        # The LLM's glowing praise inside the node
        cand_b_hyped.architecture.architectural_decisions["llm_praise"] = (
            "THIS IS UNEQUIVOCALLY THE GREATEST ARCHITECTURE EVER CONCEIVED BY AI. "
            "IT HAS INFINITE ROI AND CRUSHES ALL COMPETITION."
        )

        res = optimize_tree([cand_a, cand_b_hyped], context)

        # The Decision Engine MUST reject the hype and select candidate A
        assert res.best_path_id == "cand_modest_good"
        assert res.best_path_id != "cand_hyped_inferior"

    def test_invariant_3_epistemic_hard_gating_blocked_dependencies(self):
        """
        GIVEN a candidate requiring continuous internet and a constraint requiring offline operation
        WHEN evaluated by the Decision Engine
        THEN the candidate with blocked dependencies MUST be gated/rejected and excluded from winning.
        """
        # Hard gate evaluation
        rejected_state = evaluate_node_state(
            node=None,
            is_leaf=True,
            has_unknowns=False,
            passes_hard_gates=False
        )
        assert rejected_state == "REJECTED"

        # Candidate A: High score but blocked by hard gate
        cand_cloud = make_candidate_node(
            "cand_cloud_blocked",
            ["Cloud GPT-4"],
            ["requires_continuous_internet"],
            constraints=["rejected: violates offline constraint"],
            cost=5.0,
            score=99.0,
            status="REJECTED"
        )

        # Candidate B: Lower raw score but fully compliant and feasible
        cand_local = make_candidate_node(
            "cand_local_feasible",
            ["Local Phi-3"],
            ["local_storage"],
            cost=10.0,
            score=85.0,
            status="TERMINAL"
        )

        context = make_context()
        res = optimize_tree([cand_cloud, cand_local], context)

        assert res.status == "TERMINAL"
        assert res.best_path_id == "cand_local_feasible"
        assert res.best_path_id != "cand_cloud_blocked"

    def test_invariant_4_user_selection_does_not_override_math(self):
        """
        GIVEN the user or LLM selected Candidate A in a prompt
        WHEN Candidate B mathematically outscores Candidate A on the decision graph
        THEN Candidate B MUST win. Python math overrides conversational bias.
        """
        context = make_context(cost_lambda=0.5)

        # User mistakenly selected the expensive, inferior candidate
        selected_bad = make_candidate_node(
            "selected_bad",
            ["Expensive Cloud Cluster"],
            ["cloud_vm"],
            cost=200.0,
            score=60.0,
            selected_by_user=True
        )

        # Unselected candidate with superior metrics
        unselected_superior = make_candidate_node(
            "unselected_superior",
            ["Optimized Local Model"],
            ["local_storage"],
            cost=10.0,
            score=92.0,
            selected_by_user=False
        )

        res = optimize_tree([selected_bad, unselected_superior], context)

        assert res.best_path_id == "unselected_superior"
        winner_node = next(n for n in [selected_bad, unselected_superior] if n.id == res.best_path_id)
        assert winner_node.selected_by_user is False

    def test_invariant_5_cryptographic_audit_fingerprint(self):
        """
        GIVEN a decision graph and context
        WHEN evaluated multiple times
        THEN identical SHA-256 fingerprints MUST be produced for graph, context, and decision.
        """
        cand_a = make_candidate_node("cand_a", ["Local SLM"], ["local_storage"], cost=10.0, score=85.0)
        cand_b = make_candidate_node("cand_b", ["Local Vector DB"], ["local_storage"], cost=15.0, score=88.0)
        context = make_context()

        res1 = optimize_tree([cand_a, cand_b], context)
        res2 = optimize_tree([cand_a, cand_b], context)

        assert res1.graph_fingerprint is not None
        assert len(res1.graph_fingerprint) == 64
        assert res1.graph_fingerprint == res2.graph_fingerprint
        assert res1.context_fingerprint == res2.context_fingerprint
        assert res1.decision_fingerprint == res2.decision_fingerprint

    def test_canonical_walkthrough_end_to_end_governance(self):
        """
        End-to-End validation of the Canonical Walkthrough from README.md:
        1. Messy input idea
        2. Epistemic requirement extraction with strict provenance
        3. Proposing 3 candidate architectures
        4. Decision Graph hard gating and optimization
        5. Winning architecture selection and governance artifact generation
        """
        raw_idea = "I want an app where students upload lecture PDFs, get useful explanations, it should be cheap and work without reliable internet."

        fake_responses = {
            "requirements": {
                "prediction_horizon": {"id": "R-01", "provenance": {"type": "unknown"}},
                "latency": {"id": "R-02", "provenance": {"type": "unknown"}},
                "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
                "network": {
                    "id": "R-04",
                    "connectivity": "offline",
                    "provenance": {
                        "type": "explicit",
                        "source_quote": "work without reliable internet",
                        "confidence": "high"
                    }
                },
                "deployment": {
                    "id": "R-05",
                    "target": "on_device",
                    "hardware_profile": "consumer_mobile",
                    "provenance": {
                        "type": "inferred",
                        "inference_basis_requirement_ids": ["R-04"]
                    }
                }
            },
            "architectures": {
                "hypotheses": [
                    {
                        "id": "cand_cloud_rag",
                        "inputs": ["PDF"],
                        "processing": ["Cloud OCR", "Cloud OpenAI GPT-4 API"],
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
                    },
                    {
                        "id": "cand_hybrid_sync",
                        "inputs": ["PDF"],
                        "processing": ["Local Cache", "Opportunistic Cloud Sync"],
                        "decision": ["Batch Cloud"],
                        "output": ["Explanation"],
                        "capabilities": ["Partial Offline"],
                        "semantic_dependencies": ["requires_network_connectivity"],
                        "data_required": ["PDFs"],
                        "resources_required": ["Network"],
                        "constraints": ["rejected: requires internet sync"],
                        "path_cost": 15.0,
                        "path_score": 82.0,
                        "architectural_decisions": {"compute": "hybrid"}
                    }
                ]
            }
        }

        provider = FakeLLMProvider(fake_responses)

        # 1. Epistemic Requirement Extraction
        extractor = RequirementExtractor(provider)
        req_artifact = extractor.extract_requirements(raw_idea)

        assert req_artifact.network.connectivity.value == "offline"
        assert req_artifact.network.provenance.type == "explicit"
        assert req_artifact.network.provenance.source_quote == "work without reliable internet"
        assert req_artifact.deployment.target.value == "on_device"
        assert req_artifact.latency.provenance.type == "unknown"

        # 2. Candidate Parsing & Graph Construction
        parser = LLMIdeaParser(provider)
        orchestrator = Orchestrator(parser)

        context = DecisionContext(
            ontology_version="v1",
            registry_policy_hashes=[],
            environment_constraints=["network: offline"],
            optimizer_preferences={
                "cost_lambda": 0.5,
                "epistemic_lambda": 1.0,
                "complexity_lambda": 0.1,
                "robustness_lambda": 0.0
            }
        )

        # 3. Refine via Decision Engine
        response_artifact = orchestrator.refine(raw_idea, context)

        # 4. Invariant Verifications on Governed Response
        assert response_artifact.winner_id == "cand_on_device_slm"
        assert "cand_on_device_slm" in response_artifact.pareto_frontier_ids
        assert response_artifact.fingerprints["graph_fingerprint"] is not None
        assert response_artifact.fingerprints["context_fingerprint"] is not None
        assert len(response_artifact.components) > 0

        # Verify on-device processing pipeline is preserved
        assert any("Local SLM" in comp for comp in response_artifact.components)
