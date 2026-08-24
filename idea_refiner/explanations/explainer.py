import sys
from pathlib import Path
from typing import List, Dict, Any

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.tree.optimizer import OptimizationResult
from decision_engine.api.recommendation import RecommendationResponse
from decision_engine.tree.graph import DecisionGraph
from decision_engine.tree.tree_schemas import PathNode
from idea_refiner.explanations.schemas import ExplanationFacts, AlternativeComparison

class ArchitectureExplainer:
    def extract_facts(self, opt_result: OptimizationResult, gov_report: RecommendationResponse, decision_graph: DecisionGraph) -> ExplanationFacts:
        winner_node = decision_graph.get_node(opt_result.best_path_id) if opt_result.best_path_id else None
        
        if not winner_node:
            return ExplanationFacts(
                winner_name="None",
                winner_components="No feasible architecture found.",
                performance=0.0, cost=0.0, robustness=0.0, complexity=0.0, epistemic_risk=0,
                governance_action=gov_report.action,
                alternatives=[]
            )
            
        arch = winner_node.architecture
        components = []
        if arch.processing: components.extend(arch.processing)
        if arch.decision: components.extend(arch.decision)
        if arch.output: components.extend(arch.output)
        
        perf = winner_node.path_score or 0.0
        cost = winner_node.path_cost or 0.0
        comp = winner_node.operational_complexity or 0.0
        robust = max(0.0, 100.0 - (len(arch.semantic_dependencies) * 10))
        epistemic_risk = len(arch.semantic_dependencies)
        
        alts = []
        for alt_id in opt_result.pareto_frontier:
            if alt_id == opt_result.best_path_id:
                continue
            alt_node = decision_graph.get_node(alt_id)
            if not alt_node:
                continue
                
            alt_perf = alt_node.path_score or 0.0
            alt_cost = alt_node.path_cost or 0.0
            alt_comp = alt_node.operational_complexity or 0.0
            alt_robust = max(0.0, 100.0 - (len(alt_node.architecture.semantic_dependencies) * 10))
            
            pros = []
            cons = []
            
            if alt_cost < cost:
                pros.append(f"Lower cost (-{cost - alt_cost:.1f})")
            elif alt_cost > cost:
                cons.append(f"Higher cost (+{alt_cost - cost:.1f})")
                
            if alt_perf > perf:
                pros.append(f"Higher performance (+{alt_perf - perf:.1f})")
            elif alt_perf < perf:
                cons.append(f"Lower performance (-{perf - alt_perf:.1f})")
                
            if alt_comp < comp:
                pros.append(f"Lower complexity (-{comp - alt_comp:.1f})")
            elif alt_comp > comp:
                cons.append(f"Higher complexity (+{alt_comp - comp:.1f})")
                
            if alt_robust > robust:
                pros.append(f"Higher robustness (+{alt_robust - robust:.1f}%)")
            elif alt_robust < robust:
                cons.append(f"Lower robustness (-{robust - alt_robust:.1f}%)")
                
            if alt_node.architecture.semantic_dependencies:
                cons.append("Unresolved dependency")
                
            alts.append(AlternativeComparison(
                architecture_name=alt_id,
                status=alt_node.status,
                pros=pros,
                cons=cons
            ))
            
        return ExplanationFacts(
            winner_name=opt_result.best_path_id,
            winner_components=" + ".join(components) if components else "Unknown",
            performance=perf,
            cost=cost,
            robustness=robust,
            complexity=comp,
            epistemic_risk=epistemic_risk,
            governance_action=gov_report.action,
            alternatives=alts
        )
        
    def render_prose(self, facts: ExplanationFacts) -> str:
        lines = []
        lines.append("Recommended Architecture")
        lines.append("─────────────────────────")
        lines.append(f"{facts.winner_name}")
        lines.append(f"{facts.winner_components}")
        lines.append("")
        lines.append("Why this won")
        lines.append("─────────────")
        lines.append(f"Performance        {facts.performance:.1f}")
        lines.append(f"Cost               {facts.cost:.1f}")
        lines.append(f"Robustness         {facts.robustness:.1f}%")
        lines.append(f"Complexity         {facts.complexity:.1f}")
        lines.append(f"Epistemic risk     {facts.epistemic_risk}")
        lines.append("")
        
        if facts.alternatives:
            lines.append("Why alternatives lost")
            lines.append("──────────────────────")
            for alt in facts.alternatives:
                lines.append(f"Architecture {alt.architecture_name}")
                for pro in alt.pros:
                    lines.append(f"+ {pro}")
                for con in alt.cons:
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
