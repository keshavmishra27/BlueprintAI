from typing import Dict, Any, List
from decision_engine.tree.optimizer import optimize_tree, PathNode
from decision_engine.tree.context import DecisionContext
from decision_engine.api.recommendation import generate_recommendation
from .parsers.base import BaseIdeaParser
from .presentation import create_product_response

class Orchestrator:
    def __init__(self, parser: BaseIdeaParser, graph_generator=None):
        self.parser = parser
        self.graph_generator = graph_generator

    def _evaluate_hypothesis(self, hyp, context, idx) -> PathNode:
        from decision_engine.input_layer.schemas import ArchitectureNode
        from decision_engine.tree.optimizer import create_evaluated_path_node
        from decision_engine.tree.tree_schemas import PathNode
        
        if isinstance(hyp, PathNode):
            arch = hyp.architecture
            original_hyp = hyp
        else:
            arch = ArchitectureNode(
                inputs=getattr(hyp, 'inputs', []),
                processing=getattr(hyp, 'processing', []),
                decision=getattr(hyp, 'decision', []),
                output=getattr(hyp, 'output', []),
                capabilities=getattr(hyp, 'capabilities', []),
                semantic_dependencies=getattr(hyp, 'semantic_dependencies', []),
                data_required=getattr(hyp, 'data_required', []),
                resources_required=getattr(hyp, 'resources_required', []),
                constraints=getattr(hyp, 'constraints', []),
                architectural_decisions=getattr(hyp, 'architectural_decisions', {})
            )
            original_hyp = hyp
            
        return create_evaluated_path_node(
            arch=arch,
            context=context,
            node_id=getattr(original_hyp, 'id', None) or f"cand_{idx}",
            parent_id=getattr(original_hyp, 'parent_id', None) or "root",
            provenance=getattr(original_hyp, 'provenance', None),
            operational_complexity=getattr(original_hyp, 'operational_complexity', 0.0)
        )

    def refine(
        self, 
        idea: str, 
        context: DecisionContext, 
        current_graph_version: str = "v1"
    ) -> Dict[str, Any]:
        """
        End-to-end pipeline mapping a natural language idea to a governed architecture.
        """
        from decision_engine.tree.graph import DecisionGraph
        
        seeds = self.parser.parse_idea_to_graph(idea)
        
        if self.graph_generator:
            expanded_hypotheses = self.graph_generator.expand_seeds(seeds)
        else:
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
        
        decision_graph = DecisionGraph()
        for i, h in enumerate(expanded_hypotheses):
            node = self._evaluate_hypothesis(h, context, i)
            decision_graph.add_node(node)
            
        decision_graph.freeze()
        
        nodes_list = decision_graph.get_nodes()
        opt_result = optimize_tree(nodes_list, context, graph_version=current_graph_version)
        opt_result.graph_fingerprint = decision_graph.get_fingerprint()
        
        serialized_opt = opt_result.model_dump_json()
        gov_report = generate_recommendation(
            serialized_opt, 
            context, 
            nodes_list, 
            current_graph_version=current_graph_version
        )
        
        return create_product_response(idea, opt_result, gov_report, decision_graph)

