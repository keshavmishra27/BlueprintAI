import urllib.request
import urllib.error
import json
import time

def demo():
    # 1. Check health
    try:
        req = urllib.request.Request("http://localhost:8088/health")
        with urllib.request.urlopen(req) as response:
            print("HEALTH CHECK RESPONSE:")
            print(response.read().decode('utf-8'))
            print("-" * 40)
    except Exception as e:
        print(f"Health check failed: {e}")
        return

    # 2. Post a payload
    payload = {
        "project_name": "DemoProject",
        "tech_stack": ["Python", "FastAPI"],
        "overall_confidence": "Medium",
        "overall_assessment": "This is a demo payload sent over HTTP.",
        "checks": [
            {
                "name": "ruff",
                "status": "completed",
                "summary": "No issues found",
                "exit_code": 0
            }
        ],
        "limitations": [
            {
                "area": "security",
                "reason": "Demo limitation.",
                "impact": "None.",
                "severity": "Info"
            }
        ],
        "evidence": [
            {
                "id": "E-DEMO-1",
                "description": "This is a test evidence item.",
                "source_type": "workspace_inspection"
            }
        ],
        "categories": {
            "architecture": {
                "score": 85,
                "confidence": "High",
                "evidence_ids": ["E-DEMO-1"],
                "explanation": "Solid.",
                "highest_priority_improvement": "N/A"
            },
            "code_quality": {
                "score": 90,
                "confidence": "High",
                "evidence_ids": [],
                "explanation": "Good.",
                "highest_priority_improvement": "N/A"
            },
            "security": {
                "score": 88,
                "confidence": "High",
                "evidence_ids": [],
                "explanation": "Good.",
                "highest_priority_improvement": "N/A"
            },
            "testing_reliability": {
                "score": 60,
                "confidence": "Medium",
                "evidence_ids": [],
                "explanation": "Missing some tests.",
                "highest_priority_improvement": "N/A"
            },
            "maintainability": {
                "score": 80,
                "confidence": "High",
                "evidence_ids": [],
                "explanation": "Good.",
                "highest_priority_improvement": "N/A"
            },
            "documentation_hygiene": {
                "score": 75,
                "confidence": "Medium",
                "evidence_ids": [],
                "explanation": "Good.",
                "highest_priority_improvement": "N/A"
            }
        },
        "findings": [],
        "positive_decisions": [],
        "priorities": []
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:8088/api/analysis", 
            data=data, 
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            print("POST /api/analysis RESPONSE (Generated Result):")
            result = json.loads(response.read().decode('utf-8'))
            print(json.dumps(result, indent=2))
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Give the server a moment if it just started
    time.sleep(1)
    demo()
