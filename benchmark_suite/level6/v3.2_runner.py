import json
import requests
import sys
from pathlib import Path

# Setup paths
base_dir = Path(__file__).resolve().parent
results_dir = base_dir / "results" / "v3.2_hospital_case_01"
raw_file = results_dir / "raw_refiner_output.json"
start_resp_file = results_dir / "journey_start_response.json"

if not raw_file.exists():
    print(f"Error: {raw_file} does not exist.")
    sys.exit(1)

with open(raw_file, "r") as f:
    payload = json.load(f)

# Add session_id
payload["session_id"] = "v3.2-hospital-case-01-session"

print("Submitting JourneyStartRequest to backend...")
response = requests.post("http://127.0.0.1:8089/api/journey/start", json=payload)

if response.status_code != 200:
    print(f"Failed: {response.status_code} - {response.text}")
    sys.exit(1)

response_data = response.json()
with open(start_resp_file, "w") as f:
    json.dump(response_data, f, indent=2)

print("JourneyStartResponse received!")
print(f"Status: {response_data.get('status')}")
print(f"Selected Uncertainty ID: {response_data.get('selected_uncertainty_id')}")
print(f"Selected Uncertainty Text: {response_data.get('selected_uncertainty_text')}")
print(f"Selection Reason: {response_data.get('selection_reason')}")
print(f"Saved response to {start_resp_file}")
