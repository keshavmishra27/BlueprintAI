from backend.app.services.crews.idea_crew import (
    gather_idea_search,
    run_idea_check_crew,
    run_idea_refine_crew,
)
def check_similar_ideas(idea: str) -> dict:
    sources, context = gather_idea_search(idea)
    return run_idea_check_crew(idea, context, sources)
def refine_idea(idea: str, existing_projects: list) -> dict:
    check_payload = {"similar_projects": existing_projects}
    return run_idea_refine_crew(idea, check_payload)
