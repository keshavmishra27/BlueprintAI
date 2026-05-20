from backend.app.services.crews.swot_crew import run_swot_crew


def analyze_swot(subject_name: str, subject_type: str, description: str) -> dict:
    return run_swot_crew(subject_name, subject_type, description)
