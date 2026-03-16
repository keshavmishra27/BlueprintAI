import sys
import os
from dotenv import load_dotenv

# Add the project root to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)

# Explicitly load .env from root
dotenv_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path)

from backend.app.services.project_suggest_service import suggest_projects
from backend.app.services.mcq_service import generate_mcq

def verify_services():
    print("Testing Project Suggestion Service...")
    try:
        # Just check if it STARTS without a NameError
        # (We don't need to wait for a full LLM response if we just want to catch the NameError)
        import threading
        
        def run_test(func, *args):
            try:
                func(*args)
            except NameError as e:
                print(f"NameError detected: {e}")
            except Exception as e:
                # Other errors like connection are "fine" for this specific NameError check
                print(f"Other error (likely expected): {type(e).__name__}")
        
        # We can't easily "timeout" a blocking call without threads
        print("Checking for NameErrors in suggest_projects...")
        # Since invoke_hybrid_llm is called inside, if system_prompt is missing, 
        # it will raise NameError before the network call or at the start of it.
        # But actually, it's defined RIGHT before the call now.
        
        # Let's just run it normally but with a very small timeout if possible, 
        # or just hope Gemini is fast.
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
