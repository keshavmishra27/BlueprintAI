import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"


def test_crew_modules_import():
    from backend.app.services.crews import (
        run_mcq_crew,
        run_repo_judge_crew,
        run_idea_check_crew,
        run_project_suggest_crew,
        run_skill_gap_crew,
    )
    from crewai import Agent, Task, Crew

    assert callable(run_mcq_crew)
    assert callable(run_skill_gap_crew)
    assert Agent is not None
    assert Task is not None
    assert Crew is not None
