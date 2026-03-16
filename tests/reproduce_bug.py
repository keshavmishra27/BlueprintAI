
import sys
import os
from pydantic import ValidationError

# Add backend to path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.routers.repo_judge import JudgeResult

def reproduce_failure():
    print("Attempting to reproduce the Pydantic validation failure...")
    
    mock_result = {
        "repo_url": "https://github.com/keshavmishra27/email-automation",
        "accessibility": "public",
        "mentor_notes": "Test",
        "security_warnings": [
            "Hardcoded password in send_email.py:8"
        ]
    }
    
    try:
        validated = JudgeResult(**mock_result)
        print("Unexpectedly PASSED validation!")
    except ValidationError as e:
        print(f"Successfully REPRODUCED validation failure: {e}")

if __name__ == "__main__":
    reproduce_failure()
