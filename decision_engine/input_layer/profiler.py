from .schemas import UserIdea, ProjectProfile

def profile_user_idea(idea: UserIdea) -> ProjectProfile:
    """
    Simulates the AI Project Profiler.
    In the real engine, an LLM would analyze the 'what' and 'why' to extract these features.
    """
    print("--- PROFILING USER IDEA ---")
    print(f"WHAT: {idea.what}")
    print(f"WHY: {idea.why}")
    print(f"HOW: {idea.how}\n")
    
    # Mocking the extraction for the hospital scenario
    return ProjectProfile(
        domains=["Healthcare"],
        problem_types=["optimization", "prediction"],
        solution_types=["software", "AI-assisted"],
        primary_values=["time_reduction", "efficiency"],
        user_types=["patient", "hospital_admin"],
        constraints=["requires_historical_data"]
    )
