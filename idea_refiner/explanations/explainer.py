import sys
from pathlib import Path
from typing import List, Dict, Any

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.tree.optimizer import OptimizationResult
from decision_engine.api.recommendation import RecommendationResponse
from decision_engine.tree.graph import DecisionGraph
from decision_engine.tree.tree_schemas import PathNode
from idea_refiner.explanations.schemas import ExplanationFacts

from decision_engine.api.artifact import DecisionMetrics, CandidateEvaluation

class ArchitectureExplainer:
    def extract_facts(self, opt_result: OptimizationResult, gov_report: RecommendationResponse, decision_graph: DecisionGraph) -> ExplanationFacts:
        candidates = []
        for node in decision_graph.nodes.values():
            if node.id == "root": 
                continue
            
            metrics = None
            if node.path_score is not None or node.path_cost is not None:
                metrics = DecisionMetrics(
                    performance=node.path_score or 0.0,
                    cost=node.path_cost or 0.0,
                    robustness=max(0.0, 100.0 - (len(node.architecture.semantic_dependencies) * 10)),
                    complexity=node.operational_complexity or 0.0,
                    epistemic_risk=len(node.architecture.semantic_dependencies)
                )
            
            arch = node.architecture
            components = []
            if arch.processing: components.extend(arch.processing)
            if arch.decision: components.extend(arch.decision)
            if arch.output: components.extend(arch.output)
            
            candidates.append(CandidateEvaluation(
                candidate_id=node.id,
                architecture_components=components,
                metrics=metrics,
                status=node.status
            ))
            
        return ExplanationFacts(
            candidates_evaluated=candidates,
            pareto_frontier_ids=opt_result.pareto_frontier,
            winner_id=opt_result.best_path_id or "None",
            governance_action=gov_report.action
        )
        
    def render_prose(self, facts: ExplanationFacts) -> str:
        lines = []
        winner = next((c for c in facts.candidates_evaluated if c.candidate_id == facts.winner_id), None)
        
        if not winner:
            return "No feasible architecture found."
            
        lines.append("Recommended Architecture")
        lines.append("─────────────────────────")
        lines.append(f"{winner.candidate_id}")
        components_str = " + ".join(winner.architecture_components) if winner.architecture_components else "Unknown"
        lines.append(f"{components_str}")
        lines.append("")
        
        lines.append("Why this won")
        lines.append("─────────────")
        if winner.metrics:
            lines.append(f"Performance        {winner.metrics.performance:.1f}")
            lines.append(f"Cost               {winner.metrics.cost:.1f}")
            lines.append(f"Robustness         {winner.metrics.robustness:.1f}%")
            lines.append(f"Complexity         {winner.metrics.complexity:.1f}")
            lines.append(f"Epistemic risk     {winner.metrics.epistemic_risk}")
        else:
            lines.append("Metrics unavailable")
        lines.append("")
        
        alternatives = [c for c in facts.candidates_evaluated if c.candidate_id in facts.pareto_frontier_ids and c.candidate_id != facts.winner_id]
        if alternatives:
            lines.append("Why alternatives lost")
            lines.append("──────────────────────")
            for alt in alternatives:
                lines.append(f"Architecture {alt.candidate_id}")
                
                pros = []
                cons = []
                if alt.metrics and winner.metrics:
                    if alt.metrics.cost < winner.metrics.cost:
                        pros.append(f"Lower cost (-{winner.metrics.cost - alt.metrics.cost:.1f})")
                    elif alt.metrics.cost > winner.metrics.cost:
                        cons.append(f"Higher cost (+{alt.metrics.cost - winner.metrics.cost:.1f})")
                        
                    if alt.metrics.performance > winner.metrics.performance:
                        pros.append(f"Higher performance (+{alt.metrics.performance - winner.metrics.performance:.1f})")
                    elif alt.metrics.performance < winner.metrics.performance:
                        cons.append(f"Lower performance (-{winner.metrics.performance - alt.metrics.performance:.1f})")
                        
                    if alt.metrics.complexity < winner.metrics.complexity:
                        pros.append(f"Lower complexity (-{winner.metrics.complexity - alt.metrics.complexity:.1f})")
                    elif alt.metrics.complexity > winner.metrics.complexity:
                        cons.append(f"Higher complexity (+{alt.metrics.complexity - winner.metrics.complexity:.1f})")
                        
                    if alt.metrics.robustness > winner.metrics.robustness:
                        pros.append(f"Higher robustness (+{alt.metrics.robustness - winner.metrics.robustness:.1f}%)")
                    elif alt.metrics.robustness < winner.metrics.robustness:
                        cons.append(f"Lower robustness (-{winner.metrics.robustness - alt.metrics.robustness:.1f}%)")
                        
                    if alt.metrics.epistemic_risk > 0:
                        cons.append("Unresolved dependency")
                
                for pro in pros:
                    lines.append(f"+ {pro}")
                for con in cons:
                    lines.append(f"- {con}")
                if alt.status == "UNRESOLVED":
                    lines.append("→ HOLD_FOR_REVIEW")
                elif alt.status == "REJECTED":
                    lines.append("→ REJECTED")
                lines.append("")
                
        lines.append("Decision")
        lines.append("────────")
        lines.append(f"{facts.governance_action}")
        
        return "\n".join(lines)
        
    def explain_decision(self, opt_result: OptimizationResult, gov_report: RecommendationResponse, decision_graph: DecisionGraph) -> str:
        facts = self.extract_facts(opt_result, gov_report, decision_graph)
        return self.render_prose(facts)
