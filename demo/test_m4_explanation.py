import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from decision_engine.tree.optimizer import OptimizationResult
from decision_engine.api.recommendation import RecommendationResponse
from decision_engine.tree.graph import DecisionGraph
from decision_engine.tree.tree_schemas import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode
from idea_refiner.explanations.explainer import ArchitectureExplainer

def create_mock_arch(components, deps=None):
    if deps is None:
        deps = []
    return ArchitectureNode(
        inputs=[], processing=components, decision=[], output=[],
        capabilities=[], semantic_dependencies=deps, data_required=[],
        resources_required=[], constraints=[], architectural_decisions={}
    )

def test_m4_explanation():
    print("\n==================================================")
    print("      M4: EXPLANATION INTEGRITY TESTS             ")
    print("==================================================")
    
    graph = DecisionGraph()
    winner_node = PathNode(
        id="Cand_B", parent_id="root",
        architecture=create_mock_arch(["FastAPI", "Kafka", "PostgreSQL", "XGBoost"]),
        status="ACTIVE", path_score=91.0, path_cost=42.0, operational_complexity=31.0
    )
    alt_a = PathNode(
        id="Cand_A", parent_id="root",
        architecture=create_mock_arch(["FastAPI", "PostgreSQL"]),
        status="ACTIVE", path_score=80.0, path_cost=20.0, operational_complexity=15.0
    )
    alt_c = PathNode(
        id="Cand_C", parent_id="root",
        architecture=create_mock_arch(["FastAPI", "Redis"], deps=["Unknown streaming engine"]),
        status="UNRESOLVED", path_score=95.0, path_cost=60.0, operational_complexity=40.0
    )
    
    for node in [winner_node, alt_a, alt_c]:
        graph.add_node(node)
    graph.freeze()
    
    opt_result = OptimizationResult(
        best_path_id="Cand_B",
        best_architecture=winner_node.architecture,
        pareto_frontier=["Cand_A", "Cand_B", "Cand_C"],
        context_fingerprint="c_hash",
        graph_fingerprint=graph.get_fingerprint(),
        graph_version="v1",
        status="OPTIMAL"
    )
    
    gov_report = RecommendationResponse(
        action="RECOMMEND",
        severity="INFO",
        violations=[],
        graph_state="VALID",
        context_state="VALID",
        epistemic_state="KNOWN",
        policy_state="VALID",
        integrity_state="VALID",
        recommendation=opt_result.best_architecture
    )
    
    explainer = ArchitectureExplainer()
    
    facts = explainer.extract_facts(opt_result, gov_report, graph)
    text1 = explainer.render_prose(facts)
    
    assert "Cand_B" in text1
    assert "FastAPI + Kafka + PostgreSQL + XGBoost" in text1
    assert "Lower cost" in text1
    assert "Lower complexity" in text1
    assert "Unresolved dependency" in text1
    assert "→ HOLD_FOR_REVIEW" in text1
    print("[PASS] 1. Artifact Derivation")
    print("[PASS] 2. Relative Comparisons")
    print("[PASS] 3. Governance Surfacing")
    
    facts2 = explainer.extract_facts(opt_result, gov_report, graph)
    text2 = explainer.render_prose(facts2)
    
    assert text1 == text2, "Explanation generation is non-deterministic!"
    
    graph_mut = DecisionGraph()
    alt_a_mut = PathNode(
        id="Cand_A", parent_id="root",
        architecture=create_mock_arch(["FastAPI", "PostgreSQL"]),
        status="ACTIVE", path_score=80.0, path_cost=70.0, operational_complexity=15.0 
    )
    for node in [winner_node, alt_a_mut, alt_c]:
        graph_mut.add_node(node)
    graph_mut.freeze()
    
    facts3 = explainer.extract_facts(opt_result, gov_report, graph_mut)
    text3 = explainer.render_prose(facts3)
    
    assert text1 != text3, "Explanation did not change after artifact mutation!"
    assert "Higher cost" in text3, "Mutated artifact (higher cost) did not reflect correctly in explanation."
    
    print("[PASS] 4. Explanation Integrity (Deterministic and reacts to artifact mutation)")
    print("\nALL 4 M4 ACCEPTANCE TESTS PASSED.")

if __name__ == "__main__":
    test_m4_explanation()
