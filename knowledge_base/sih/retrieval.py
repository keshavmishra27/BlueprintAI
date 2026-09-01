import json
from pathlib import Path
from typing import List, Dict, Any

def load_json_files(dir_path: Path) -> List[Dict]:
    records = []
    if dir_path.exists():
        for f in dir_path.glob("*.json"):
            with open(f, "r", encoding="utf-8") as file:
                records.append(json.load(file))
    return records

def profile_idea(query: str) -> Dict[str, Any]:
    """
    Mock of the future AI Project Profiler.
    In the real system, an LLM would extract this from the query.
    """
    print(f"Profiling Idea: '{query}'")
    
    if "hospital" in query.lower() and "waiting time" in query.lower():
        return {
            "domain": ["Healthcare"],
            "subdomains": ["Hospital Operations", "Scheduling"],
            "decision_features": {
                "problem_type": ["optimization", "prediction"],
                "solution_type": ["software", "AI-assisted"],
                "primary_value": ["time_reduction", "efficiency"]
            }
        }
    return {}

def calculate_relevance(project: Dict, profile: Dict) -> int:
    """Calculates a simple overlap score between project features and profile."""
    score = 0
    
    if any(d in project.get("problem_domain", []) for d in profile.get("domains", profile.get("domain", []))):
        score += 10
        
    p_features = project.get("decision_features", {})
    
    if "decision_features" in profile:
        profile_features = profile["decision_features"]
        key_map = [("problem_type", "problem_type"), ("solution_type", "solution_type"), ("primary_value", "primary_value")]
    else:
        profile_features = profile
        key_map = [("problem_type", "problem_types"), ("solution_type", "solution_types"), ("primary_value", "primary_values")]
    
    for proj_key, prof_key in key_map:
        overlap = set(p_features.get(proj_key, [])).intersection(set(profile_features.get(prof_key, [])))
        score += len(overlap) * 5
        
    return score

def retrieve_projects(profile: Dict, all_projects: List[Dict], top_k: int = 3) -> List[Dict]:
    scored_projects = []
    for p in all_projects:
        score = calculate_relevance(p, profile)
        if score > 0:
            scored_projects.append({"score": score, "project": p})
            
    scored_projects.sort(key=lambda x: x["score"], reverse=True)
    return scored_projects[:top_k]

def retrieve_patterns(project_ids: List[str], all_patterns: List[Dict]) -> List[Dict]:
    relevant_patterns = []
    for pattern in all_patterns:
        overlap = set(pattern.get("observed_in_projects", [])).intersection(set(project_ids))
        if overlap:
            pattern_copy = pattern.copy()
            pattern_copy["triggered_by"] = list(overlap)
            relevant_patterns.append(pattern_copy)
    return relevant_patterns

def run_experiment():
    base_dir = Path(__file__).resolve().parent
    normalized_dir = base_dir / "normalized"
    patterns_dir = base_dir / "patterns"
    
    all_projects = load_json_files(normalized_dir)
    all_patterns = load_json_files(patterns_dir)
    
    query = "I want to build an AI system to reduce hospital patient waiting time."
    
    profile = profile_idea(query)
    print("\n--- PROJECT PROFILER OUTPUT ---")
    print(json.dumps(profile, indent=2))
    
    top_projects = retrieve_projects(profile, all_projects)
    print("\n--- RELEVANT SIH PROJECTS ---")
    project_ids = []
    for sp in top_projects:
        p = sp["project"]
        project_ids.append(p["id"])
        print(f"\nID: {p['id']} (Relevance Score: {sp['score']})")
        print(f"What: {p['what']}")
        print(f"Why selected: Overlap in {p['decision_features']['problem_type']} & {p['decision_features']['primary_value']}")
        
    relevant_patterns = retrieve_patterns(project_ids, all_patterns)
    print("\n--- RELEVANT PATTERNS ---")
    for pat in relevant_patterns:
        print(f"\nPattern: {pat['pattern']}")
        print(f"Triggered by: {pat['triggered_by']}")
        print("Evidence:")
        for ev in pat['evidence']:
            print(f"  - {ev}")

if __name__ == "__main__":
    run_experiment()
