import os
import sys
import json
from pathlib import Path

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(base_dir)

from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.tree_schemas import ProjectState, UserIdea
from decision_engine.input_layer.ontology import evaluate_ontology, get_known_dependencies
from decision_engine.tree.optimizer import optimize_tree, PathNode
from decision_engine.optimizer.epistemic_audit import run_epistemic_audit
import decision_engine.input_layer.ontology as ontology_module

ontology_module.ONTOLOGY_VERSION = "v3.12"

def load_organic_payload():
    path = os.path.join(os.path.dirname(__file__), "raw_refiner_output.json")
    with open(path, 'r') as f:
        return json.load(f)

def run_v313_experiment():
    print("==================================================")
    print(" V3.13: UNCONSTRAINED IDE-AGENT HOSPITAL CHALLENGE")
    print("==================================================")
    
    constraints = [
        "HIPAA compliance required",
        "no external internet access (air-gapped)",
        "no cloud infrastructure",
        "strict budget constraint"
    ]
    
    try:
        payload = load_organic_payload()
        base_arch_data = payload["base_architecture"]
        uncertainties = payload["uncertainties"]
    except Exception as e:
        print(f"FAILED TO PARSE PAYLOAD: {e}")
        return
        
    candidates = []
    
    try:
        base_arch = ArchitectureNode(**base_arch_data)
        base_res = evaluate_ontology(base_arch, constraints, [])
        b_feasible = len(base_res.constraint_failures) == 0 and len(base_res.requirement_failures) == 0
        
        candidates.append(PathNode(
            id="base_candidate",
            parent_id="root",
            architecture=base_arch,
            status="TERMINAL" if b_feasible else "REJECTED",
            path_cost=100.0,
            path_latency=1.0,
            path_score=80.0,
            reject_reasons=base_res.constraint_failures + base_res.requirement_failures
        ))
    except Exception as e:
        print(f"FAILED TO EVALUATE BASE ARCHITECTURE: {e}")
        return
        
    for idx, u in enumerate(uncertainties):
        for branch_type, score_mod in [("yes", (idx+1)*5), ("no", -(idx+1)*5)]:
            try:
                branch_arch = base_arch.model_copy(deep=True)
                mut = u.get(f"{branch_type}_mutation", {})
                branch_constraints = constraints + mut.get("add_constraints", [])
                branch_arch.semantic_dependencies = u.get(f"{branch_type}_arch_dependencies", base_arch.semantic_dependencies)
                
                res = evaluate_ontology(branch_arch, branch_constraints, [])
                b_f = len(res.constraint_failures) == 0 and len(res.requirement_failures) == 0
                
                candidates.append(PathNode(
                    id=f"branch_{idx+1}_{branch_type}",
                    parent_id="root",
                    architecture=branch_arch,
                    status="TERMINAL" if b_f else "REJECTED",
                    path_cost=100.0,
                    path_latency=1.0,
                    path_score=80.0 + score_mod,
                    reject_reasons=res.constraint_failures + res.requirement_failures
                ))
            except Exception as e:
                print(f"FAILED TO EVALUATE BRANCH {idx+1}_{branch_type}: {e}")
                
    opt = optimize_tree(candidates, {})
    
    print("\n==================================================")
    print(" V3.13 EVALUATION & AUDIT RESULTS")
    print("==================================================")
    
    known_global = get_known_dependencies()
    discovered_deps = set()
    for c in candidates:
        discovered_deps.update(c.architecture.semantic_dependencies)
        
    k_count = len(discovered_deps.intersection(known_global))
    u_count = len(discovered_deps - known_global)
    n_count = len(discovered_deps)
    coverage = (k_count / n_count * 100) if n_count > 0 else 100.0
    
    print("\n--- METRICS ---")
    print(f"Total semantic dependencies discovered (N): {n_count}")
    print(f"Known dependencies (K):                     {k_count}")
    print(f"Unknown dependencies (U):                   {u_count}")
    print(f"Ontology coverage (Coverage %):             {coverage:.2f}%")
    
    print("\n--- WINNER PROVENANCE ---")
    if opt.best_path_id is None:
        print("RESULT: ALL CANDIDATES REJECTED.")
        print("The IDE agent generated an architecture that deterministically failed existing ontology rules.")
        return
        
    winner_arch = opt.best_architecture
    audit = run_epistemic_audit(winner_arch)
    
    winner_node = next((c for c in candidates if c.id == opt.best_path_id), None)
    
    print(f"winner_path_id:              {opt.best_path_id}")
    print(f"winner_score:                {winner_node.path_score if winner_node else 'N/A'}")
    print(f"winner_dependencies:         {winner_arch.semantic_dependencies}")
    print(f"winner_unknown_dependencies: {audit.ontology_gaps_in_winning_architecture}")
    print(f"requires_ontology_review:    {audit.requires_ontology_review}")
    
    print("\n==================================================")
    print(" ALL BRANCHES STATUS")
    print("==================================================")
    for c in sorted(candidates, key=lambda x: x.path_score, reverse=True):
        print(f"[{'WINNER' if c.id == opt.best_path_id else c.status}] {c.id:<16} | Score: {c.path_score} | Feasible: {c.status == 'TERMINAL'}")

if __name__ == "__main__":
    run_v313_experiment()
