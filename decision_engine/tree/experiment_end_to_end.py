import sys
import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement, UserIdea
from decision_engine.tree.tree_schemas import ArchitectureState, ProjectState, TreeState, DecisionTraceEntry
from decision_engine.input_layer.evaluator import evaluate_battle
from decision_engine.tree.experiment_llm_adapters import llm_baseline, llm_generate_player_b, llm_find_uncertainties
from decision_engine.tree.question_generator import select_best_question
from decision_engine.tree.tree_runner import SimulatedUser
from knowledge_base.sih.retrieval import load_json_files, retrieve_projects, retrieve_patterns

DOMAINS = [
    {
        "name": "Hospital Waiting Time",
        "idea": UserIdea(
            what="Reduce hospital patient waiting time.",
            why="Patients wait because appointments and hospital resources aren't coordinated.",
            how_raw="Maintain a queue and use an LLM to predict appointment timing.",
            how_structured=ArchitectureNode(
                inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[]
            )
        ),
        "requirements": [
            Requirement(name="Reduce waiting time", required=True),
            Requirement(name="Handle resource bottlenecks", required=True)
        ],
        "profile": {
            "domain": ["Healthcare"],
            "decision_features": {
                "problem_type": ["optimization", "prediction"],
                "solution_type": ["software", "AI-assisted"],
                "primary_value": ["time_reduction", "efficiency"]
            }
        },
        "simulated_constraints": ["missing historical data"],
        "initial_constraints": ["hospital intranet available"]
    },
    {
        "name": "Agriculture/Crop Disease",
        "idea": UserIdea(
            what="Detect crop diseases early.",
            why="Farmers lose yield because they notice disease too late.",
            how_raw="Use drones to take pictures and a cloud AI model to classify diseases.",
            how_structured=ArchitectureNode(
                inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[]
            )
        ),
        "requirements": [
            Requirement(name="High accuracy detection", required=True),
            Requirement(name="Operate in rural areas", required=True)
        ],
        "profile": {
            "domain": ["Agriculture"],
            "decision_features": {
                "problem_type": ["classification", "monitoring"],
                "solution_type": ["AI-assisted", "hardware"],
                "primary_value": ["yield_protection"]
            }
        },
        "simulated_constraints": ["no cloud", "limited compute", "intermittent connectivity"],
        "initial_constraints": ["drones available"]
    },
    {
        "name": "Education/Personalized Learning",
        "idea": UserIdea(
            what="Provide personalized tutoring to students.",
            why="Students learn at different paces and need custom curriculum.",
            how_raw="Build a centralized AI tutor that stores all student history and adapts curriculum.",
            how_structured=ArchitectureNode(
                inputs=[], processing=[], decision=[], output=[], capabilities=[], data_required=[], resources_required=[], constraints=[]
            )
        ),
        "requirements": [
            Requirement(name="Adapt to student level", required=True),
            Requirement(name="Track student progress", required=True)
        ],
        "profile": {
            "domain": ["Education"],
            "decision_features": {
                "problem_type": ["personalization"],
                "solution_type": ["AI-assisted"],
                "primary_value": ["learning_outcome"]
            }
        },
        "simulated_constraints": ["no external storage", "strict student privacy", "limited access to personal history"],
        "initial_constraints": ["school tablets available"]
    }
]

def load_kb():
    kb_dir = Path(base_dir) / "knowledge_base" / "sih"
    return load_json_files(kb_dir / "normalized"), load_json_files(kb_dir / "patterns")

def format_kb_evidence(projects, patterns):
    evidence_str = "Relevant Past SIH Winning Projects:\n"
    for sp in projects:
        p = sp['project']
        evidence_str += f"- ID: {p['id']}\n  What: {p['what']}\n  Why they won: {p['why_it_won']}\n"
    
    evidence_str += "\nRelevant Architectural Patterns:\n"
    for pat in patterns:
        evidence_str += f"- Pattern: {pat['pattern']}\n  Evidence: {pat['evidence']}\n"
        
    return evidence_str

def calculate_metrics(final_arch: ArchitectureNode, project_state: ProjectState, requirements: list[Requirement], trace: list[DecisionTraceEntry], kb_ids: set):
    battle = evaluate_battle(final_arch, final_arch, project_state.current_constraints, requirements)
    
    constraint_satisfaction = len(project_state.current_constraints) - len(battle.b_constraint_violations)
    total_constraints = len(project_state.current_constraints)
    
    decisions = final_arch.processing + final_arch.decision + final_arch.output
    
    supported = [d for d in final_arch.evidence_provenance if d in kb_ids]
    supported_count = len(supported)
    unsupported_count = len(final_arch.evidence_provenance) - supported_count
    
    total_decisions = len(decisions)
    
    return {
        "constraint_violations": len(battle.b_constraint_violations),
        "constraint_satisfaction_num": constraint_satisfaction,
        "constraint_satisfaction_den": total_constraints,
        "evidence_supported": supported_count,
        "evidence_unsupported": unsupported_count,
        "adaptations": len(trace),
        "questions": len(trace)
    }

def run_experiment():
    all_projects, all_patterns = load_kb()
    
    output_log = []
    
    for domain in DOMAINS:
        print(f"\n==================================================")
        print(f"{domain['name'].upper()}")
        print(f"==================================================\n")
        output_log.append(f"==================================================\n{domain['name'].upper()}\n==================================================\n")
        
        print("Running Baseline...")
        baseline_constraints = domain['initial_constraints'] + domain['simulated_constraints']
        baseline_arch = llm_baseline(domain['idea'], baseline_constraints)
        
        baseline_battle = evaluate_battle(baseline_arch, baseline_arch, baseline_constraints, domain['requirements'])
        baseline_violations = len(baseline_battle.b_constraint_violations)
        baseline_sat = len(baseline_constraints) - baseline_violations
        
        baseline_output = "BASELINE\nArchitecture:\n" + " -> ".join(baseline_arch.processing + baseline_arch.decision) + "\n\n"
        baseline_output += f"Constraint violations:\n{baseline_violations}\n\n"
        baseline_output += f"Constraint satisfaction:\n{baseline_sat}/{len(baseline_constraints)}\n\n"
        baseline_output += "Evidence:\n0/0 (Baseline has no KB access)\n\n--------------------------------------------------\n"
        
        print(baseline_output)
        output_log.append(baseline_output)
        
        print("Running Adaptive System...")
        top_projects = retrieve_projects(domain['profile'], all_projects, top_k=3)
        project_ids = [sp['project']['id'] for sp in top_projects]
        relevant_patterns = retrieve_patterns(project_ids, all_patterns)
        
        kb_evidence_text = format_kb_evidence(top_projects, relevant_patterns)
        
        kb_id_set = set(project_ids + [p['pattern'] for p in relevant_patterns])
        
        adaptive_output = f"ADAPTIVE SYSTEM\n\nRetrieved SIH evidence:\n{len(top_projects)} projects\n{len(relevant_patterns)} patterns\n\n"
        
        p_state = ProjectState(
            user_idea=domain['idea'],
            current_constraints=domain['initial_constraints'].copy(),
            current_requirements=domain['requirements']
        )
        
        simulated_user = SimulatedUser(domain['simulated_constraints'])
        
        print("Generating Initial Player B...")
        b_response = llm_generate_player_b(p_state, kb_evidence_text)
        b_arch_state = ArchitectureState(
            architecture=b_response.architecture,
            generation=1,
            based_on=b_response.based_on
        )
        
        adaptive_output += f"Initial Player B:\n{' -> '.join(b_arch_state.architecture.processing + b_arch_state.architecture.decision)}\n\n"
        
        tree_state = TreeState(
            current_state_id="level_0",
            project_state=p_state,
            user_architecture=b_arch_state,
            player_b_architecture=b_arch_state,
            battle_history=[evaluate_battle(b_arch_state.architecture, b_arch_state.architecture, p_state.current_constraints, p_state.current_requirements)]
        )
        
        decision_trace = []
        depth = 0
        MAX_DEPTH = 4
        
        while depth < MAX_DEPTH:
            depth += 1
            print(f"Level {depth}: Finding uncertainties...")
            uncertainties = llm_find_uncertainties(tree_state.player_b_architecture.architecture, tree_state.project_state)
            
            if not uncertainties:
                break
                
            
            eval_uncs = []
            for unc in uncertainties[:2]:
                print(f"  Simulating branches for: {unc.unknown_fact}")
                yes_mut = StateMutation(add_constraints=[unc.question_target + " available"], remove_constraints=[])
                no_mut = StateMutation(add_constraints=["no " + unc.question_target], remove_constraints=[])
                
                mock_state_yes = copy.deepcopy(tree_state.project_state)
                mock_state_yes.current_constraints.extend(yes_mut.add_constraints)
                yes_arch = llm_generate_player_b(mock_state_yes, kb_evidence_text, tree_state.player_b_architecture.architecture, f"Constraint added: {yes_mut.add_constraints}")
                yes_battle = evaluate_battle(tree_state.user_architecture.architecture, yes_arch.architecture, mock_state_yes.current_constraints, mock_state_yes.current_requirements)
                
                mock_state_no = copy.deepcopy(tree_state.project_state)
                mock_state_no.current_constraints.extend(no_mut.add_constraints)
                no_arch = llm_generate_player_b(mock_state_no, kb_evidence_text, tree_state.player_b_architecture.architecture, f"Constraint added: {no_mut.add_constraints}")
                no_battle = evaluate_battle(tree_state.user_architecture.architecture, no_arch.architecture, mock_state_no.current_constraints, mock_state_no.current_requirements)
                
                f_change = yes_battle.b_feasible != no_battle.b_feasible
                w_change = yes_battle.winner != no_battle.winner
                a_change = " -> ".join(yes_arch.architecture.processing) != " -> ".join(no_arch.architecture.processing)
                
                unc.decision_impact_score = int(f_change) + int(w_change) + int(a_change)
                
                from decision_engine.tree.tree_schemas import BranchOutcome, UncertaintyImpact
                unc.yes_outcome = BranchOutcome(b_feasible=yes_battle.b_feasible, winner=yes_battle.winner.value, architecture_name="->".join(yes_arch.architecture.processing), architecture_capabilities=[])
                unc.no_outcome = BranchOutcome(b_feasible=no_battle.b_feasible, winner=no_battle.winner.value, architecture_name="->".join(no_arch.architecture.processing), architecture_capabilities=[])
                
                eval_uncs.append(unc)
                
            q_node = select_best_question(eval_uncs)
            
            if not q_node or q_node.uncertainty.decision_impact_score == 0:
                break
                
            user_answer = simulated_user.answer_question(q_node)
            mutation = q_node.options[user_answer]
            
            new_constraints = [c for c in mutation.add_constraints if c not in tree_state.project_state.current_constraints]
            if not new_constraints:
                break
                
            tree_state.project_state.current_constraints.extend(new_constraints)
            
            print(f"Adapting Player B due to {user_answer}...")
            new_b_resp = llm_generate_player_b(tree_state.project_state, kb_evidence_text, tree_state.player_b_architecture.architecture, f"Constraint added: {new_constraints}")
            
            trace_entry = DecisionTraceEntry(
                question_text=q_node.question_text,
                why_selected=f"Impact={q_node.uncertainty.decision_impact_score}",
                user_answer=user_answer,
                state_mutation=new_constraints,
                architecture_before=" -> ".join(tree_state.player_b_architecture.architecture.processing),
                architecture_after=" -> ".join(new_b_resp.architecture.processing),
                battle_before=tree_state.battle_history[-1].winner.value,
                battle_after=""
            )
            
            tree_state.player_b_architecture = ArchitectureState(
                architecture=new_b_resp.architecture,
                generation=tree_state.player_b_architecture.generation + 1,
                based_on=new_b_resp.based_on
            )
            
            new_battle = evaluate_battle(tree_state.user_architecture.architecture, tree_state.player_b_architecture.architecture, tree_state.project_state.current_constraints, tree_state.project_state.current_requirements)
            tree_state.battle_history.append(new_battle)
            trace_entry.battle_after = new_battle.winner.value
            
            decision_trace.append(trace_entry)
            
            adaptive_output += f"Question:\n\"{q_node.question_text}\"\n\nImpact:\n{q_node.uncertainty.decision_impact_score}\n\n"
            adaptive_output += f"User:\n{user_answer}\n\nState mutation:\n+ {new_constraints}\n\n"
            adaptive_output += f"Player B v{tree_state.player_b_architecture.generation}:\n{' -> '.join(tree_state.player_b_architecture.architecture.processing)}\n\n"
            
        metrics = calculate_metrics(tree_state.player_b_architecture.architecture, tree_state.project_state, domain['requirements'], decision_trace, kb_id_set)
        
        adaptive_output += f"Constraint satisfaction:\n{metrics['constraint_satisfaction_num']}/{metrics['constraint_satisfaction_den']}\n\n"
        adaptive_output += f"Evidence-supported:\n{metrics['evidence_supported']}\nUnsupported:\n{metrics['evidence_unsupported']}\n\n"
        adaptive_output += f"Adaptations:\n{metrics['adaptations']}\n\nQuestions:\n{metrics['questions']}\n\n"
        
        print(adaptive_output)
        output_log.append(adaptive_output)
        
    with open(Path(base_dir) / "experiment_results.txt", "w", encoding="utf-8") as f:
        f.write("".join(output_log))

if __name__ == "__main__":
    import copy
    run_experiment()
