import sys
import os
from dotenv import load_dotenv
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)
dotenv_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path)
from backend.app.services.project_suggest_service import suggest_projects
from backend.app.services.mcq_service import generate_mcq
def verify_services():
    print("Testing Project Suggestion Service...")
    try:
        import threading
        def run_test(func, *args):
            try:
                func(*args)
            except NameError as e:
                print(f"NameError detected: {e}")
            except Exception as e:
                print(f"Other error (likely expected): {type(e).__name__}")
        print("Checking for NameErrors in suggest_projects...")
        res = suggest_projects("Sustainability")
        if "resume_projects" in res:
            print("Cleanup: suggest_projects is FUNCTIONAL and prompts are defined.")
        print("\nChecking for NameErrors in generate_mcq...")
        res_mcq = generate_mcq("Python")
        if len(res_mcq) > 0:
            print("Cleanup: generate_mcq is FUNCTIONAL and prompts are defined.")
    except Exception as e:
        print(f"Verification failed with unexpected error: {e}")
if __name__ == "__main__":
    verify_services()