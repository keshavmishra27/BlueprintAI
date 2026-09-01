import sys
import json
from pathlib import Path

project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from decision_engine.tree.context import DecisionContext
from idea_refiner.orchestrator import Orchestrator
from invoke_idea_refiner import HospitalPredictionParser

def main():
    idea = "Build a hospital overcrowding prediction system that predicts emergency-department overcrowding several hours in advance using historical patient-flow data and real-time hospital data. The system should provide predictions that hospital administrators can use for staffing and resource planning."
    
    context = DecisionContext(
        ontology_version="1.0.0",
        registry_policy_hashes=[],
        environment_constraints=[],
        architecture={},
        business_context={},
        optimizer_preferences={
            "cost_lambda": 1.0, 
            "complexity_lambda": 1.0
        }
    )
    
    parser = HospitalPredictionParser()
    orchestrator = Orchestrator(parser)
    
    seeds = orchestrator.parser.parse_idea_to_graph(idea)
    
    expanded_hypotheses = []
    for i, s in enumerate(seeds):
        if hasattr(s, 'id') and getattr(s, 'id'):
            expanded_hypotheses.append(s)
        else:
            if hasattr(s, 'model_copy'):
                s = s.model_copy(update={"id": f"seed_{i}"})
            else:
                s.id = f"seed_{i}"
            expanded_hypotheses.append(s)
            
    from decision_engine.tree.graph import DecisionGraph
    decision_graph = DecisionGraph()
    for i, h in enumerate(expanded_hypotheses):
        node = orchestrator._evaluate_hypothesis(h, context, i)
        decision_graph.add_node(node)
        
    decision_graph.freeze()
    nodes_list = decision_graph.get_nodes()
    
    from decision_engine.tree.optimizer import optimize_tree
    opt_result = optimize_tree(nodes_list, context, graph_version="v1")
    opt_result.graph_fingerprint = decision_graph.get_fingerprint()
    
    print("\n=== OPTIMIZATION RESULT ===")
    print(opt_result.model_dump_json(indent=2))
    
    decision_artifact = orchestrator.refine(idea, context)
    print("\n=== ARCHITECTURE DECISION ARTIFACT ===")
    with open("trace_artifact.json", "w", encoding="utf-8") as f:
        f.write(decision_artifact.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
