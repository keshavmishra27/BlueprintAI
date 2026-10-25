import os
import sys
import json

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from decision_engine.tree.context import DecisionContext
from idea_refiner.parsers.deterministic import DeterministicIdeaParser
from idea_refiner.orchestrator import Orchestrator

def print_test(name, result, expected_action):
    action = result.get("governance", {}).get("action")
    passed = (action == expected_action)
    print(f"{'PASS' if passed else 'FAIL'} | {name.ljust(50)} | Exp: {expected_action.ljust(15)} | Act: {action}")
    if not passed:
        print(f"Full result:\n{json.dumps(result, indent=2)}")
        raise AssertionError(f"Test {name} failed.")

def run_tests():
    print("==================================================")
    print(" IDEA REFINER: END-TO-END ORCHESTRATION")
    print("==================================================")
    
    parser = DeterministicIdeaParser()
    orchestrator = Orchestrator(parser)
    
    ctx = DecisionContext(
        project_id="P1",
        ontology_version="v3.12",
        registry_policy_hashes=[],
        environment_constraints=[],
        current_constraints=[],
        current_requirements=[],
        historical_decisions=[],
        available_resources=[],
        optimizer_preferences={
            "epistemic_lambda": 10.0,
            "robustness_lambda": 10.0,
            "cost_lambda": 1.0,
            "complexity_lambda": 1.0,
            "robustness_strategy": "raw"
        },
        future_scenarios=[]
    )
    
    res_a = orchestrator.refine("hospital overcrowding prediction", ctx)
    print_test("A. Clean idea", res_a, "RECOMMEND")
    
    res_b = orchestrator.refine("unresolved hospital overcrowding prediction", ctx)
    print_test("B. Unresolved candidate wins mathematically", res_b, "HOLD_FOR_REVIEW")
    
    pass

class DriftingOrchestrator(Orchestrator):
    def refine(self, idea: str, context: DecisionContext, current_graph_version: str = "v1"):
        from decision_engine.tree.optimizer import optimize_tree
        from decision_engine.api.recommendation import generate_recommendation
        from idea_refiner.presentation import create_product_response
        import copy
        
        decision_graph = self.parser.parse_idea_to_graph(idea)
        
        opt_result = optimize_tree(decision_graph, context, graph_version=current_graph_version)
        
        drifted_ctx = copy.deepcopy(context)
        drifted_ctx.environment_constraints = ["drifted_constraint"]
        
        drifted_graph = copy.deepcopy(decision_graph)
        drifted_graph[1].architecture.semantic_dependencies = ["drifted_dependency"]
        
        serialized_opt = opt_result.model_dump_json()
        gov_report = generate_recommendation(
            serialized_opt, 
            drifted_ctx, 
            drifted_graph, 
            current_graph_version=current_graph_version
        )
        
        return create_product_response(opt_result, gov_report)

def run_test_c():
    ctx = DecisionContext(
        project_id="P1",
        ontology_version="v3.12",
        registry_policy_hashes=[],
        environment_constraints=[],
        current_constraints=[],
        current_requirements=[],
        historical_decisions=[],
        available_resources=[],
        optimizer_preferences={
            "epistemic_lambda": 10.0,
            "robustness_lambda": 10.0,
            "cost_lambda": 1.0,
            "complexity_lambda": 1.0,
            "robustness_strategy": "raw"
        },
        future_scenarios=[]
    )
    
    parser = DeterministicIdeaParser()
    drifting_orchestrator = DriftingOrchestrator(parser)
    
    res_c = drifting_orchestrator.refine("hospital overcrowding prediction", ctx)
    print_test("C. Graph/context drift", res_c, "HOLD_FOR_REVIEW")
    
    assert "STALE_DECISION_CONTEXT" in res_c["governance"]["violations"]
    assert "STALE_DECISION_GRAPH" in res_c["governance"]["violations"]
    
if __name__ == "__main__":
    run_tests()
    run_test_c()
    print("\nALL ACCEPTANCE CRITERIA MET.")
