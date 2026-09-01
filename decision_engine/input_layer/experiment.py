import sys
from pathlib import Path
import json

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import UserIdea
from decision_engine.input_layer.profiler import profile_user_idea
from decision_engine.input_layer.player_b import generate_player_b_response

from knowledge_base.sih.retrieval import retrieve_projects, retrieve_patterns, load_json_files

def main():
    print("==================================================")
    print("    WHAT -> WHY -> HOW Input Layer Experiment     ")
    print("==================================================\n")
    
    idea = UserIdea(
        what="Reduce hospital waiting time",
        why="Patients spend too long waiting because resources aren't coordinated.",
        how="Maintain a queue and use an LLM to predict appointment timing."
    )
    
    profile = profile_user_idea(idea)
    
    kb_dir = base_dir / "knowledge_base" / "sih"
    all_projects = load_json_files(kb_dir / "normalized")
    all_patterns = load_json_files(kb_dir / "patterns")
    
    print("\n--- RETRIEVING EVIDENCE FROM KNOWLEDGE BASE ---")
    top_projects = retrieve_projects(profile.model_dump(), all_projects)
    project_ids = [p["project"]["id"] for p in top_projects]
    relevant_patterns = retrieve_patterns(project_ids, all_patterns)
    print(f"Retrieved {len(top_projects)} projects and {len(relevant_patterns)} patterns.")
    
    print("\n")
    response = generate_player_b_response(idea, [p["project"] for p in top_projects], relevant_patterns)
    
    print("\n==================================================")
    print("                 BATTLE RESULTS                   ")
    print("==================================================")
    
    print(f"\nYOUR APPROACH:\n{response.user_approach}")
    
    print(f"\nPLAYER B's SELECTED ARCHITECTURE:\n{response.selected_approach}")
    
    print(f"\n{response.architectural_difference}")
    
    print("\nADVANTAGES:")
    for adv in response.advantages:
        print(f"  + {adv}")
        
    print("\nTRADEOFFS:")
    for t in response.tradeoffs:
        print(f"  - {t}")
        
    print(f"\nCONFIDENCE: {response.confidence}")
    
    print("\nEVIDENCE CHAIN:")
    for ev in response.evidence:
        print(f"  Decision: {ev.decision}")
        print(f"  Source Project: {ev.source_project}")
        print(f"  Pattern: {ev.supporting_pattern}")
        print(f"  Evidence: {ev.evidence}\n")
        
if __name__ == "__main__":
    main()
