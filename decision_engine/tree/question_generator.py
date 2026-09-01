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
from decision_engine.input_layer.evaluator import evaluate_battle

def _evaluate_branch_hypothesis(
    project_state: ProjectState, 
    user_arch_state: ArchitectureState, 
    candidate_architecture: ArchitectureNode, 
    mutation: StateMutation
) -> BranchOutcome:
    """
    Evaluates how the hypothesis architecture performs if the given mutation is applied.
    """
    mock_state = copy.deepcopy(project_state)
    mock_state.current_constraints.extend(mutation.add_constraints)
    mock_state.current_constraints = [c for c in mock_state.current_constraints if c not in mutation.remove_constraints]
    
    battle_result = evaluate_battle(
        user_arch_state.architecture, 
        candidate_architecture, 
        mock_state.current_constraints, 
        mock_state.current_requirements
    )
    
    return BranchOutcome(
        b_feasible=battle_result.b_feasible,
        winner=battle_result.winner.value,
        architecture_name=" -> ".join(candidate_architecture.processing),
        architecture_capabilities=candidate_architecture.capabilities
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
        
        yes_outcome = _evaluate_branch_hypothesis(project_state, user_arch_state, agent_unc.yes_candidate_architecture, agent_unc.yes_mutation)
        no_outcome = _evaluate_branch_hypothesis(project_state, user_arch_state, agent_unc.no_candidate_architecture, agent_unc.no_mutation)
        
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
        "YES": AnswerOption(mutation=agent_unc.yes_mutation, candidate_architecture=agent_unc.yes_candidate_architecture),
        "NO": AnswerOption(mutation=agent_unc.no_mutation, candidate_architecture=agent_unc.no_candidate_architecture)
    }
        
    return QuestionNode(
        id=f"q_{top_unc.id[:8]}",
        question_text=agent_unc.question_text,
        uncertainty=top_unc,
        options=options
    )
