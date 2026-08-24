import sys
import copy
import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement, UserIdea
from decision_engine.tree.tree_schemas import ArchitectureState, ProjectState, TreeState, PathNode
from decision_engine.input_layer.evaluator import evaluate_battle
from decision_engine.tree.experiment_llm_adapters import llm_baseline, llm_generate_player_b, llm_find_uncertainties
from decision_engine.tree.question_generator import select_best_question
from decision_engine.tree.tree_runner import SimulatedUser
from decision_engine.tree.optimizer import optimize_tree, evaluate_node_state
from knowledge_base.sih.retrieval import load_json_files, retrieve_projects, retrieve_patterns
from decision_engine.tree.experiment_end_to_end import load_kb, format_kb_evidence, DOMAINS

import uuid
import hashlib

def canonicalize_architecture(arch: ArchitectureNode) -> str:
    """
    Creates a canonical representation of an architecture to measure true architectural diversity,
    avoiding superficial text differences. We categorize the processing steps.
    """
    decisions = arch.architectural_decisions
    if not decisions:
        # Fallback for older nodes or if LLM failed to generate it
        sorted_caps = sorted(arch.capabilities)
        sorted_res = sorted(arch.resources_required)
        return f"CAPS:{','.join(sorted_caps)}|RES:{','.join(sorted_res)}"
    
    keys = sorted(decisions.keys())
    parts = [f"{k}={decisions[k]}" for k in keys]
    return "DECISIONS:" + "|".join(parts)

def run_generative_diversity_experiment(domain_index: int = 1, N: int = 3):
    domain = DOMAINS[domain_index]
    all_projects, all_patterns = load_kb()
    
    # Baseline
    print("==================================================")
    print(f"RUNNING BASELINE FOR: {domain['name']}")
    print("==================================================")
    baseline_constraints = domain['initial_constraints'] + domain['simulated_constraints']
    baseline_arch = llm_baseline(domain['idea'], baseline_constraints)
    baseline_battle = evaluate_battle(baseline_arch, baseline_arch, baseline_constraints, domain['requirements'])
    
    # Assign mock cost/value to baseline for scoring
    baseline_cost = 100.0 # mock
    baseline_value = 80.0 if baseline_battle.b_feasible else 0.0
    baseline_score = baseline_value - (baseline_cost / 100.0 * 100 * 0.5)
    
    print(f"Baseline Feasible: {baseline_battle.b_feasible}")
    print(f"Baseline Score: {baseline_score}")
    print(f"Baseline Canonical: {canonicalize_architecture(baseline_arch)}\n")
    
    # Preparation for Adaptive Runs
    top_projects = retrieve_projects(domain['profile'], all_projects, top_k=3)
    project_ids = [sp['project']['id'] for sp in top_projects]
    relevant_patterns = retrieve_patterns(project_ids, all_patterns)
    kb_evidence_text = format_kb_evidence(top_projects, relevant_patterns)
    
    global_f_union = {} # dict of arch_id -> canonical_str
    global_canonical_patterns = set()
    
    run_metrics = []
    
    for i in range(N):
        print(f"\n==================================================")
        print(f"RUN {i+1}/{N}")
        print(f"==================================================")
        
        p_state = ProjectState(
            user_idea=domain['idea'],
            current_constraints=domain['initial_constraints'].copy(),
            current_requirements=domain['requirements']
        )
        simulated_user = SimulatedUser(domain['simulated_constraints'])
        
        b_response = llm_generate_player_b(p_state, kb_evidence_text)
        b_arch_state = ArchitectureState(architecture=b_response.architecture, generation=1, based_on=b_response.based_on)
        
        tree_state = TreeState(
            current_state_id=f"run_{i}_level_0",
            project_state=p_state,
            user_architecture=b_arch_state,
            player_b_architecture=b_arch_state,
            battle_history=[evaluate_battle(b_arch_state.architecture, b_arch_state.architecture, p_state.current_constraints, p_state.current_requirements)],
            decision_graph=[]
        )
        
        depth = 0
        MAX_DEPTH = 2 # Keeping depth small to reduce API calls for N runs
        questions_asked = 0
        
        root_node = PathNode(
            id=str(uuid.uuid4()),
            parent_id=None,
            architecture=b_arch_state.architecture,
            status="ACTIVE",
            selected_by_user=True,
            path_cost=80.0,
            path_value=90.0 if tree_state.battle_history[-1].b_feasible else 0.0
        )
        tree_state.decision_graph.append(root_node)
        current_node_id = root_node.id
        
        while depth < MAX_DEPTH:
            depth += 1
            uncertainties = llm_find_uncertainties(tree_state.player_b_architecture.architecture, tree_state.project_state)
            
            if not uncertainties:
                break
                
            eval_uncs = []
            for unc in uncertainties[:1]: # Limit to 1 uncertainty to save LLM cost in this experiment
                from decision_engine.tree.tree_schemas import StateMutation, BranchOutcome
                
                yes_mut = StateMutation(add_constraints=[unc.question_target + " available"], remove_constraints=[])
                no_mut = StateMutation(add_constraints=["no " + unc.question_target], remove_constraints=[])
                
                # Mock YES branch
                mock_state_yes = copy.deepcopy(tree_state.project_state)
                mock_state_yes.current_constraints.extend(yes_mut.add_constraints)
                yes_arch = llm_generate_player_b(mock_state_yes, kb_evidence_text, tree_state.player_b_architecture.architecture, f"Constraint added: {yes_mut.add_constraints}")
                yes_battle = evaluate_battle(tree_state.user_architecture.architecture, yes_arch.architecture, mock_state_yes.current_constraints, mock_state_yes.current_requirements)
                
                # Mock NO branch
                mock_state_no = copy.deepcopy(tree_state.project_state)
                mock_state_no.current_constraints.extend(no_mut.add_constraints)
                no_arch = llm_generate_player_b(mock_state_no, kb_evidence_text, tree_state.player_b_architecture.architecture, f"Constraint added: {no_mut.add_constraints}")
                no_battle = evaluate_battle(tree_state.user_architecture.architecture, no_arch.architecture, mock_state_no.current_constraints, mock_state_no.current_requirements)
                
                yes_node = PathNode(
                    id=str(uuid.uuid4()),
                    parent_id=current_node_id,
                    architecture=yes_arch.architecture,
                    status=evaluate_node_state(None, is_leaf=True, has_unknowns=False, passes_hard_gates=yes_battle.b_feasible),
                    selected_by_user=False,
                    path_cost=90.0,
                    path_value=95.0 if yes_battle.b_feasible else 0.0
                )
                
                no_node = PathNode(
                    id=str(uuid.uuid4()),
                    parent_id=current_node_id,
                    architecture=no_arch.architecture,
                    status=evaluate_node_state(None, is_leaf=True, has_unknowns=False, passes_hard_gates=no_battle.b_feasible),
                    selected_by_user=False,
                    path_cost=70.0,
                    path_value=90.0 if no_battle.b_feasible else 0.0
                )
                
                tree_state.decision_graph.extend([yes_node, no_node])
                
                f_change = yes_battle.b_feasible != no_battle.b_feasible
                w_change = yes_battle.winner != no_battle.winner
                a_change = " -> ".join(yes_arch.architecture.processing) != " -> ".join(no_arch.architecture.processing)
                unc.decision_impact_score = int(f_change) + int(w_change) + int(a_change)
                
                unc.yes_outcome = BranchOutcome(b_feasible=yes_battle.b_feasible, winner=yes_battle.winner.value, architecture_name=yes_node.id, architecture_capabilities=[])
                unc.no_outcome = BranchOutcome(b_feasible=no_battle.b_feasible, winner=no_battle.winner.value, architecture_name=no_node.id, architecture_capabilities=[])
                eval_uncs.append(unc)
                
            q_node = select_best_question(eval_uncs)
            
            if not q_node or q_node.uncertainty.decision_impact_score == 0:
                break
                
            questions_asked += 1
            user_answer = simulated_user.answer_question(q_node)
            mutation = q_node.options[user_answer]
            
            new_constraints = [c for c in mutation.add_constraints if c not in tree_state.project_state.current_constraints]
            if not new_constraints:
                break
                
            tree_state.project_state.current_constraints.extend(new_constraints)
            
            selected_arch_id = q_node.uncertainty.yes_outcome.architecture_name if user_answer == "YES" else q_node.uncertainty.no_outcome.architecture_name
            for node in tree_state.decision_graph:
                if node.id == selected_arch_id:
                    node.selected_by_user = True
                    if depth < MAX_DEPTH:
                        node.status = "ACTIVE"
                    current_node_id = node.id
                    tree_state.player_b_architecture.architecture = node.architecture
                    break
        
        res = optimize_tree(tree_state.decision_graph, {'weight_cost': 0.5, 'weight_value': 0.5})
        
        total_generated = len(tree_state.decision_graph)
        total_rejected = len([n for n in tree_state.decision_graph if n.status == "REJECTED"])
        terminal_nodes = [n for n in tree_state.decision_graph if n.status == "TERMINAL"]
        
        patterns_in_run = set([canonicalize_architecture(n.architecture) for n in terminal_nodes])
        global_canonical_patterns.update(patterns_in_run)
        
        f_i_dict = {n.id: canonicalize_architecture(n.architecture) for n in terminal_nodes}
        global_f_union.update(f_i_dict)
        
        unselected_winner = False
        blueprint_score = 0
        if res.best_path_id:
            best_node = next(n for n in tree_state.decision_graph if n.id == res.best_path_id)
            unselected_winner = not best_node.selected_by_user
            blueprint_score = best_node.path_score
            
        metrics = {
            "total_candidates": total_generated,
            "rejected_candidates": total_rejected,
            "terminal_candidates": len(terminal_nodes),
            "distinct_patterns": len(patterns_in_run),
            "unselected_winner": unselected_winner,
            "questions_asked": questions_asked,
            "blueprint_score": blueprint_score,
            "blueprint_feasible": "TERMINAL" in best_node.status if res.best_path_id else False,
            "delta_score": blueprint_score - baseline_score,
            "f_i": list(set(f_i_dict.values())) # store unique canonical patterns
        }
        run_metrics.append(metrics)
        
        print(f"Run {i+1} completed: {total_generated} generated, {total_rejected} rejected, {len(terminal_nodes)} terminal.")

    print("\n==================================================")
    print("EXPERIMENT RESULTS")
    print("==================================================")
    print(f"Baseline Score: {baseline_score}")
    print(f"Total Unique Canonical Patterns Discovered (Global F_union): {len(global_canonical_patterns)}")
    
    print("\n==================================================")
    print("WARNING: Coverage Interpretation")
    print("==================================================")
    print("Candidate-space coverage is relative to the union of architectures generated during the experiment, not coverage of all possible architectures.")
    print("Coverage measures consistency against the experimentally discovered candidate space.")

    for i, m in enumerate(run_metrics):
        coverage = len(m["f_i"]) / len(global_canonical_patterns) if global_canonical_patterns else 0
        delta_feasibility = int(m['blueprint_feasible']) - int(baseline_battle.b_feasible)

        print(f"\n--- RUN {i+1} ---")
        print(f"Candidates Generated: {m['total_candidates']}")
        print(f"Terminal Candidates (F): {m['terminal_candidates']}")
        print(f"Distinct Patterns: {m['distinct_patterns']}")
        print(f"Coverage of Global Candidate Space: {coverage*100:.1f}%")
        print(f"Information Gaps (Questions): {m['questions_asked']}")
        print(f"Unselected Branch Won: {m['unselected_winner']}")
        print(f"BlueprintAI Score: {m['blueprint_score']:.2f}")
        print(f"Delta Score vs Baseline: {m['delta_score']:.2f}")
        print(f"Delta Feasibility vs Baseline: {delta_feasibility}")

if __name__ == "__main__":
    run_generative_diversity_experiment(domain_index=1, N=3)
