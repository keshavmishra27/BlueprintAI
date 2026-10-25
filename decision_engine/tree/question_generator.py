import copy
from typing import Optional, List, Dict
import uuid

from decision_engine.tree.tree_schemas import (
    ArchitectureState, 
    ProjectState, 
    ArchitectureNode,
    ArchitecturalUncertainty, 
    QuestionNode, 
    StateMutation,
    BranchOutcome,
    UncertaintyImpact,
    AgentUncertainty,
    AnswerOption
)
from decision_engine.input_layer.evaluator import _evaluate_core

def _evaluate_branch_hypothesis(
    project_state: ProjectState, 
    user_arch_state: ArchitectureState, 
    candidate_hypothesis, # can be UnvalidatedArchitectureHypothesis
    mutation: StateMutation
) -> BranchOutcome:
    """
    Evaluates how the hypothesis architecture performs if the given mutation is applied.
    """
    mock_state = copy.deepcopy(project_state)
    mock_state.current_constraints.extend(mutation.add_constraints)
    mock_state.current_constraints = [c for c in mock_state.current_constraints if c not in mutation.remove_constraints]
    
    # Convert UnvalidatedArchitectureHypothesis to ArchitectureNode for evaluation
    if hasattr(candidate_hypothesis, "model_dump"):
        candidate_dict = candidate_hypothesis.model_dump(exclude={"id", "parent_id", "generation_reason", "source", "hypothesis", "path_cost", "path_score", "operational_complexity", "provenance"})
        # Filter out fields that don't belong to ArchitectureNode
        arch_fields = ArchitectureNode.model_fields.keys()
        filtered_dict = {k: v for k, v in candidate_dict.items() if k in arch_fields}
        candidate_architecture = ArchitectureNode(**filtered_dict)
    else:
        candidate_architecture = candidate_hypothesis

    battle_result = _evaluate_core(
        user_arch_state.architecture, 
        candidate_architecture, 
        mock_state.current_constraints, 
        mock_state.current_requirements
    )
    
    return BranchOutcome(
        b_feasible=battle_result.b_feasible,
        winner=battle_result.winner.value,
        architecture_name=" -> ".join(candidate_architecture.processing),
        architecture_capabilities=[cap.name for cap in candidate_architecture.capabilities] if candidate_architecture.capabilities else []
    )

def evaluate_provided_uncertainties(
    agent_uncertainties: List[AgentUncertainty],
    player_b_arch_state: ArchitectureState, 
    user_arch_state: ArchitectureState, 
    project_state: ProjectState
) -> List[ArchitecturalUncertainty]:
    """
    Evaluates uncertainties proposed by the Agent against the current deterministic reality.
    """
    evaluated_uncertainties = []
    
    for agent_unc in agent_uncertainties:
        unc = ArchitecturalUncertainty(
            id=agent_unc.id,
            question_target=agent_unc.question_target,
            unknown_fact=agent_unc.unknown_fact,
            affected_architectures=[f"player_b_v{player_b_arch_state.generation}"],
            possible_impacts=[],
            importance=agent_unc.importance
        )
        
        yes_outcome = _evaluate_branch_hypothesis(project_state, user_arch_state, agent_unc.yes_hypothesis, agent_unc.yes_mutation)
        no_outcome = _evaluate_branch_hypothesis(project_state, user_arch_state, agent_unc.no_hypothesis, agent_unc.no_mutation)
        
        feasibility_changed = yes_outcome.b_feasible != no_outcome.b_feasible
        winner_changed = yes_outcome.winner != no_outcome.winner
        architecture_changed = yes_outcome.architecture_name != no_outcome.architecture_name or \
                               yes_outcome.architecture_capabilities != no_outcome.architecture_capabilities
        
        score = int(feasibility_changed) * 10 + int(winner_changed) * 5 + int(architecture_changed) * 2
        if unc.importance.lower() == "high":
            score += 3
        elif unc.importance.lower() == "medium":
            score += 1
            
        unc.yes_outcome = yes_outcome
        unc.no_outcome = no_outcome
        unc.impact_analysis = UncertaintyImpact(
            feasibility_changed=feasibility_changed,
            winner_changed=winner_changed,
            architecture_changed=architecture_changed, 
            decision_impact_score=score
        )
        unc.decision_impact_score = score
        
        evaluated_uncertainties.append(unc)
        
    return evaluated_uncertainties

def select_best_question(
    evaluated_uncertainties: List[ArchitecturalUncertainty],
    agent_uncertainties_map: Dict[str, AgentUncertainty]
) -> Optional[QuestionNode]:
    """
    Ranks uncertainties by their decision_impact_score and returns the QuestionNode for the highest.
    """
    if not evaluated_uncertainties:
        return None
        
    evaluated_uncertainties.sort(key=lambda x: x.decision_impact_score, reverse=True)
    
    top_unc = evaluated_uncertainties[0]
    
    if top_unc.decision_impact_score == 0:
        return None
        
    agent_unc = agent_uncertainties_map.get(top_unc.id)
    if not agent_unc:
        return None
        
    options = {
        "YES": AnswerOption(mutation=agent_unc.yes_mutation, hypothesis=agent_unc.yes_hypothesis),
        "NO": AnswerOption(mutation=agent_unc.no_mutation, hypothesis=agent_unc.no_hypothesis)
    }
        
    return QuestionNode(
        id=f"q_{top_unc.id[:8]}",
        question_text=agent_unc.question_text,
        uncertainty=top_unc,
        options=options
    )
