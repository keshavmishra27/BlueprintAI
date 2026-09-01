from typing import Dict, Any
from decision_engine.tree.optimizer import OptimizationResult
from decision_engine.api.recommendation import RecommendationResponse
from decision_engine.tree.graph import DecisionGraph
from decision_engine.api.artifact import ArchitectureDecisionArtifact

def create_product_response(idea: str, opt_result: OptimizationResult, gov_report: RecommendationResponse, decision_graph: DecisionGraph = None) -> ArchitectureDecisionArtifact:
    """
    Combines the underlying optimization result and the governance artifact
    into the product-facing payload.
    """
    human_readable = ""
    candidates = []
    if decision_graph:
        from idea_refiner.explanations.explainer import ArchitectureExplainer
        explainer = ArchitectureExplainer()
        facts = explainer.extract_facts(opt_result, gov_report, decision_graph)
        human_readable = explainer.render_prose(facts)
        candidates = facts.candidates_evaluated
        
    arch = opt_result.best_architecture
    
    components = []
    databases = []
    if arch and arch.processing:
        components.extend(arch.processing)
        for c in arch.processing:
            c_lower = c.lower()
            if "sql" in c_lower or "mongo" in c_lower or "redis" in c_lower or "database" in c_lower or "db" in c_lower:
                databases.append(c)
                
    interfaces = []
    if arch:
        interfaces.extend(arch.inputs or [])
        interfaces.extend(arch.output or [])
        
    return ArchitectureDecisionArtifact(
        decision_id=opt_result.best_path_id or "",
        idea=idea,
        winner_id=opt_result.best_path_id or "",
        candidates_evaluated=candidates,
        pareto_frontier_ids=opt_result.pareto_frontier,
        components=components,
        technologies=components,
        databases=databases,
        interfaces=interfaces,
        data_flows=[],
        decisions=arch.architectural_decisions if arch else {},
        constraints=arch.constraints if arch else [],
        dependencies=arch.semantic_dependencies if arch else [],
        governance={
            "action": gov_report.action,
            "severity": gov_report.severity,
            "violations": gov_report.violations,
            "graph_state": gov_report.graph_state,
            "context_state": gov_report.context_state,
            "epistemic_state": gov_report.epistemic_state,
            "policy_state": gov_report.policy_state,
            "integrity_state": gov_report.integrity_state
        },
        fingerprints={
            "context_fingerprint": opt_result.context_fingerprint,
            "graph_fingerprint": opt_result.graph_fingerprint,
            "graph_version": opt_result.graph_version
        },
        explanation=human_readable
    )
