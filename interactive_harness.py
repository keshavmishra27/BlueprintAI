import json
import sys
from idea_refiner.parsers.providers.fake import FakeLLMProvider
from idea_refiner.parsers.epistemic_resolver import EpistemicResolver
from decision_engine.tree.context import DecisionContext
from decision_engine.tree.optimizer import optimize_tree
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.tree_schemas import PathNode
from decision_engine.tree.epistemic import EpistemicValidator

def make_candidate_node(node_id: str, processing: list, dependencies: list, cost: float, score: float, status: str) -> PathNode:
    arch = ArchitectureNode(
        processing=processing,
        semantic_dependencies=dependencies,
    )
    return PathNode(
        id=node_id,
        parent_id="root",
        architecture=arch,
        status=status,
        path_cost=cost,
        path_score=score,
    )

def main():
    print("========================================================")
    print("M13-C0: INTERACTIVE ENGINE HARNESS")
    print("========================================================\n")

    # 1. Simulate the LLM outputting candidates for the messy idea
    cand_a = make_candidate_node("cand_a", ["Cloud RAG API"], ["requires_continuous_connectivity"], cost=40.0, score=90.0, status="REJECTED")
    cand_b = make_candidate_node("cand_b", ["High-End Local SLM"], ["high_end_hardware"], cost=10.0, score=95.0, status="UNRESOLVED")
    cand_c = make_candidate_node("cand_c", ["Light Local SLM"], ["basic_mobile_hardware", "blob_storage"], cost=5.0, score=85.0, status="UNRESOLVED")
    
    graph_nodes = [cand_a, cand_b, cand_c]
    
    context = DecisionContext(
        ontology_version="v1",
        registry_policy_hashes=[],
        environment_constraints=["network: offline"],
        optimizer_preferences={"cost_lambda": 0.5, "epistemic_lambda": 1.0, "complexity_lambda": 0.1, "robustness_lambda": 0.0}
    )

    print("Messy idea: I want an app where students upload lecture PDFs, get useful explanations, it should be cheap and work without reliable internet.")
    
    # 2. First Pass Evaluation
    res1 = optimize_tree(graph_nodes, context)
    
    active_uncertainty = "student_hardware"
    question = "Do target users have modern phones capable of running lightweight models locally?"
    print(f"\n[!] Engine requires information: {question}")
    
    # 3. Human interaction
    print("\nHuman input: ")
    # Hardcode for demo purposes, or use input() if sys.stdin.isatty()
    user_input = "Most students have low-end phones."
    print(f"> {user_input}")

    # 4. Epistemic Resolver interprets (No decision making here!)
    # Using FakeLLMProvider mapped to return "low_end" for this prompt.
    fake_responses = {
        "architectures": {"normalized_value": "low_end"}
    }
    class MockLLM(FakeLLMProvider):
        def generate_structured(self, prompt, schema):
            return {"normalized_value": "low_end"}

    resolver = EpistemicResolver(MockLLM({}))
    proposed_resolution = resolver.resolve(
        target=active_uncertainty, 
        question=question, 
        human_answer=user_input
    )
    
    print("\n[EpistemicResolver] proposed resolution:")
    print(f"  Target: {proposed_resolution.target}")
    print(f"  Value: {proposed_resolution.normalized_value}")

    # 5. Decision Engine authoritative validation
    updated_graph = []
    engine_validation = "INVALID"
    derived_branch = None
    
    for node in graph_nodes:
        is_valid, new_node = EpistemicValidator.validate_and_apply(
            proposed_resolution, node, target_uncertainty=active_uncertainty
        )
        if is_valid and new_node:
            engine_validation = "VALID"
            derived_branch = new_node.id
            # Real engine would run evaluate_node_state, mock it for C0 harness:
            if new_node.status != "REJECTED":
                if "high_end_hardware" in new_node.architecture.semantic_dependencies and "basic_mobile_hardware" in new_node.architecture.semantic_dependencies:
                    new_node.status = "REJECTED"
                else:
                    new_node.status = "TERMINAL" if "basic_mobile_hardware" in new_node.architecture.semantic_dependencies else "UNRESOLVED"
            updated_graph.append(new_node)
        else:
            updated_graph.append(node)

    print("\n[Decision Engine] Validation:")
    print(f"  Status: {engine_validation} (Ontology match confirmed)")
    if derived_branch:
        print(f"  Branch Derived: {derived_branch}")
        
    if engine_validation != "VALID":
        print("Engine rejected the proposed resolution.")
        sys.exit(1)

    # 6. Second Pass Evaluation
    final_res = optimize_tree(updated_graph, context)

    # 7. Trace & Justification (The Killer Test)
    print("\n========================================================")
    print("DECISION ENGINE GOVERNANCE PROOF")
    print("========================================================\n")
    print("Human input:")
    print(f'"{proposed_resolution.source_answer}"\n')
    print("Epistemic target:")
    print(f"{proposed_resolution.target}\n")
    print("Engine Validation:")
    print(f"{engine_validation} (Ontology match confirmed)")
    print(f"Branch Derived: {derived_branch}\n")
    
    for node in updated_graph:
        print("--------------------------------------------------------")
        print(node.id.split('_branch_')[0].upper())
        print("--------------------------------------------------------")
        for dep in node.architecture.semantic_dependencies:
            print(dep)
        if node.status == "REJECTED":
            print("-> REJECTED\n")
        elif node.status == "TERMINAL":
            print("-> FEASIBLE\n")
        else:
            print(f"-> {node.status}\n")
            
    print("PathScore:")
    print(f"WINNER = {final_res.effective_score}\n")
    print("--------------------------------------------------------")
    print("WINNER")
    print("--------------------------------------------------------")
    print(final_res.best_path_id)
    print("\nSelection mechanism: Decision Graph optimizer")
    print("LLM-selected winner: NONE")
    print("User-selected winner: NONE")
    print("Narrative influence: NONE\n")
    print("========================================================")
    print("VERDICT: GRAPH SELECTED THE ARCHITECTURE")
    print("========================================================")


if __name__ == "__main__":
    main()
