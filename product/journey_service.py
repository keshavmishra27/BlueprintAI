import sys
import copy
from typing import Dict, Any, List, Optional
from pathlib import Path
import uuid

base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import UserIdea, ArchitectureNode, Requirement
from decision_engine.tree.tree_schemas import (
    ProjectState, ArchitectureState, TreeState, DecisionTraceEntry, 
    StateMutation, BranchOutcome, QuestionNode, AgentUncertainty, 
    ArchitecturalUncertainty, UncertaintyImpact, AnswerOption, PathNode
)
from decision_engine.input_layer.evaluator import evaluate_battle, EvalStatus

def serialize_pydantic_obj(obj):
    return obj.model_dump() if obj else None

class JourneyService:
    def __init__(self):
        pass

    def _evaluate_branch(self, 
                         project_state: ProjectState, 
                         user_arch: ArchitectureNode,
                         candidate_arch: ArchitectureNode, 
                         mutation: StateMutation) -> BranchOutcome:
        mock_state = copy.deepcopy(project_state)
        mock_state.current_constraints.extend(mutation.add_constraints)
        mock_state.current_constraints = [c for c in mock_state.current_constraints if c not in mutation.remove_constraints]
        
        battle = evaluate_battle(user_arch, candidate_arch, mock_state.current_constraints, mock_state.current_requirements)
        
        return BranchOutcome(
            b_feasible=battle.b_feasible,
            winner=battle.winner.value,
            architecture_name=" -> ".join(candidate_arch.processing),
            architecture_capabilities=candidate_arch.capabilities,
            b_dimensions={
                "constraint": battle.b_dimensions.constraint.value if battle.b_dimensions else "UNKNOWN",
                "requirement": battle.b_dimensions.requirement.value if battle.b_dimensions else "UNKNOWN",
                "performance": battle.b_dimensions.performance.value if battle.b_dimensions else "UNKNOWN",
                "cost": battle.b_dimensions.cost.value if battle.b_dimensions else "UNKNOWN",
                "timeline": battle.b_dimensions.timeline.value if battle.b_dimensions else "UNKNOWN"
            } if battle.b_dimensions else None
        )

    def _process_uncertainties(self, 
                               tree_state: TreeState, 
                               agent_uncertainties: List[AgentUncertainty]) -> Optional[QuestionNode]:
        if not agent_uncertainties:
            return None
            
        evaluated_uncs = []
        for agent_unc in agent_uncertainties:
            yes_outcome = self._evaluate_branch(tree_state.project_state, tree_state.user_architecture.architecture, agent_unc.yes_candidate_architecture, agent_unc.yes_mutation)
            no_outcome = self._evaluate_branch(tree_state.project_state, tree_state.user_architecture.architecture, agent_unc.no_candidate_architecture, agent_unc.no_mutation)
            
            feasibility_changed = yes_outcome.b_feasible != no_outcome.b_feasible
            winner_changed = yes_outcome.winner != no_outcome.winner
            architecture_changed = yes_outcome.architecture_name != no_outcome.architecture_name
            
            score = int(feasibility_changed) + int(winner_changed) + int(architecture_changed)
            
            unc = ArchitecturalUncertainty(
                id=agent_unc.id,
                question_target=agent_unc.question_target,
                unknown_fact=agent_unc.unknown_fact,
                affected_architectures=[f"player_b_v{tree_state.player_b_architecture.generation}"],
                possible_impacts=[],
                importance=agent_unc.importance,
                yes_outcome=yes_outcome,
                no_outcome=no_outcome,
                impact_analysis=UncertaintyImpact(
                    feasibility_changed=feasibility_changed,
                    winner_changed=winner_changed,
                    architecture_changed=architecture_changed,
                    decision_impact_score=score
                ),
                decision_impact_score=score
            )
            evaluated_uncs.append((unc, agent_unc))
            
        evaluated_uncs.sort(key=lambda x: x[0].decision_impact_score, reverse=True)
        top_unc, original_agent_unc = evaluated_uncs[0]
        
        if top_unc.decision_impact_score == 0:
            return None
            
        return QuestionNode(
            id=f"q_{top_unc.id[:8]}",
            question_text=original_agent_unc.question_text,
            uncertainty=top_unc,
            options={
                "YES": AnswerOption(mutation=original_agent_unc.yes_mutation, candidate_architecture=original_agent_unc.yes_candidate_architecture),
                "NO": AnswerOption(mutation=original_agent_unc.no_mutation, candidate_architecture=original_agent_unc.no_candidate_architecture)
            }
        )
        
    def _compute_path_scores(self, tree_state: TreeState) -> Optional[str]:
        prefs = tree_state.optimization_preferences or {}
        
        val_w = 1.0
        cost_w = 0.5
        time_w = 0.5
        
        if "path_objective" in prefs:
            po = prefs["path_objective"]
            val_w = po.get("value_weight", val_w)
            cost_w = po.get("cost_weight", cost_w)
            time_w = po.get("timeline_weight", time_w)
        elif "prioritize" in prefs:
            prioritize = prefs["prioritize"]
            if "cost" in prioritize: cost_w = 2.0
            if "timeline" in prioritize: time_w = 2.0
            if "value" in prioritize: val_w = 2.0
            
        best_score = float('-inf')
        best_id = None
        
        for node in tree_state.decision_graph:
            if node.dimension_evaluation:
                if any(v == "FAIL" for k, v in node.dimension_evaluation.items()):
                    continue
                    
            val = len(node.architecture.capabilities) * 10
            
            c = 0
            if node.architecture.cost and node.architecture.cost.get("estimated_prototype_cost"):
                c = node.architecture.cost.get("estimated_prototype_cost")
                
            t = 0
            if node.architecture.timeline and node.architecture.timeline.get("estimated_days"):
                t = node.architecture.timeline.get("estimated_days")
                
            score = (val * val_w) - (c * cost_w) - (t * time_w)
            
            node.path_value = val
            node.path_cost = c
            node.path_score = score
            
            if score > best_score:
                best_score = score
                best_id = node.id
                
        return best_id

    def start_journey(self, what: str, why: str, how: str, 
                      constraints: List[str],
                      requirements_dicts: List[Dict],
                      gemini_baseline_dict: Dict,
                      player_b_arch_dict: Dict, 
                      uncertainties_dicts: List[Dict],
                      optimization_preferences: Optional[Dict] = None) -> Dict[str, Any]:
                      
        baseline_node = ArchitectureNode.model_validate(gemini_baseline_dict)
        idea = UserIdea(
            what=what, why=why, how_raw=how,
            how_structured=baseline_node
        )
        
        reqs = [Requirement.model_validate(r) for r in requirements_dicts]
        
        p_state = ProjectState(
            user_idea=idea,
            current_constraints=constraints,
            current_requirements=reqs
        )
        
        player_b_node = ArchitectureNode.model_validate(player_b_arch_dict)
        b_arch_state = ArchitectureState(
            architecture=player_b_node,
            generation=1,
            based_on="Gemini generation"
        )
        
        user_arch = ArchitectureState(
            architecture=idea.how_structured,
            generation=1,
            based_on="User input"
        )
        
        battle = evaluate_battle(user_arch.architecture, b_arch_state.architecture, p_state.current_constraints, p_state.current_requirements)
        
        root_id = str(uuid.uuid4())
        
        root_node = PathNode(
            id=root_id,
            parent_id=None,
            architecture=b_arch_state.architecture,
            status="ACTIVE",
            dimension_evaluation={
                "constraint": battle.b_dimensions.constraint.value if battle.b_dimensions else "UNKNOWN",
                "requirement": battle.b_dimensions.requirement.value if battle.b_dimensions else "UNKNOWN",
                "performance": battle.b_dimensions.performance.value if battle.b_dimensions else "UNKNOWN",
                "cost": battle.b_dimensions.cost.value if battle.b_dimensions else "UNKNOWN",
                "timeline": battle.b_dimensions.timeline.value if battle.b_dimensions else "UNKNOWN"
            } if hasattr(battle, 'b_dimensions') and battle.b_dimensions else None
        )
        
        tree_state = TreeState(
            current_state_id=root_id,
            project_state=p_state,
            user_architecture=user_arch,
            player_b_architecture=b_arch_state,
            battle_history=[battle],
            decision_graph=[root_node],
            optimization_preferences=optimization_preferences
        )
        
        agent_uncertainties = [AgentUncertainty.model_validate(u) for u in uncertainties_dicts]
        q_node = self._process_uncertainties(tree_state, agent_uncertainties)
        
        best_path_id = self._compute_path_scores(tree_state)
        
        return {
            "is_complete": q_node is None,
            "tree_state": tree_state,
            "current_question": q_node,
            "best_path_id": best_path_id
        }

    def answer_question(self, tree_state: TreeState, q_node: QuestionNode, selected_option: str, 
                        new_player_b_arch_dict: Optional[Dict], 
                        new_uncertainties_dicts: Optional[List[Dict]]) -> Dict[str, Any]:
                        
        if selected_option not in q_node.options:
            raise ValueError(f"Invalid option: {selected_option}")
            
        ans_opt = q_node.options[selected_option]
        
        new_constraints = [c for c in ans_opt.mutation.add_constraints if c not in tree_state.project_state.current_constraints]
        if new_constraints:
            tree_state.project_state.current_constraints.extend(new_constraints)
            
        tree_state.project_state.current_constraints = [c for c in tree_state.project_state.current_constraints if c not in ans_opt.mutation.remove_constraints]
            
        if new_player_b_arch_dict:
            new_arch_node = ArchitectureNode.model_validate(new_player_b_arch_dict)
        else:
            new_arch_node = tree_state.player_b_architecture.architecture
            
        arch_before = " -> ".join(tree_state.player_b_architecture.architecture.processing)
        arch_after = " -> ".join(new_arch_node.processing)
        
        tree_state.player_b_architecture = ArchitectureState(
            architecture=new_arch_node,
            generation=tree_state.player_b_architecture.generation + 1,
            based_on="Gemini adaptation"
        )
        
        new_battle = evaluate_battle(tree_state.user_architecture.architecture, tree_state.player_b_architecture.architecture, tree_state.project_state.current_constraints, tree_state.project_state.current_requirements)
        
        battle_before = tree_state.battle_history[-1].winner.value
        tree_state.battle_history.append(new_battle)
        
        new_id = str(uuid.uuid4())
        
        new_node = PathNode(
            id=new_id,
            parent_id=tree_state.current_state_id,
            architecture=new_arch_node,
            question_that_produced_it=q_node.question_text,
            user_answer=selected_option,
            state_mutation=new_constraints,
            status="ACTIVE",
            dimension_evaluation={
                "constraint": new_battle.b_dimensions.constraint.value if new_battle.b_dimensions else "UNKNOWN",
                "requirement": new_battle.b_dimensions.requirement.value if new_battle.b_dimensions else "UNKNOWN",
                "performance": new_battle.b_dimensions.performance.value if new_battle.b_dimensions else "UNKNOWN",
                "cost": new_battle.b_dimensions.cost.value if new_battle.b_dimensions else "UNKNOWN",
                "timeline": new_battle.b_dimensions.timeline.value if new_battle.b_dimensions else "UNKNOWN"
            } if hasattr(new_battle, 'b_dimensions') and new_battle.b_dimensions else None
        )
        
        tree_state.decision_graph.append(new_node)
        tree_state.current_state_id = new_id
        
        trace_entry = DecisionTraceEntry(
            question_text=q_node.question_text,
            why_selected=f"Impact={q_node.uncertainty.decision_impact_score}",
            user_answer=selected_option,
            state_mutation=new_constraints,
            architecture_before=arch_before,
            architecture_after=arch_after,
            battle_before=battle_before,
            battle_after=new_battle.winner.value
        )
        
        agent_uncertainties = [AgentUncertainty.model_validate(u) for u in (new_uncertainties_dicts or [])]
        next_q_node = self._process_uncertainties(tree_state, agent_uncertainties)
        
        best_path_id = self._compute_path_scores(tree_state)
        
        return {
            "is_complete": next_q_node is None,
            "tree_state": tree_state,
            "current_question": next_q_node,
            "trace_entry": trace_entry,
            "best_path_id": best_path_id
        }
