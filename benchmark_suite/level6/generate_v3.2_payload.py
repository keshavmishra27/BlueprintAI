import json
import copy

def get_base_arch():
    return {
        "inputs": ["historical hospital operational data"],
        "processing": ["predictive model"],
        "decision": ["overcrowding risk assessment"],
        "output": ["local hospital dashboard"],
        "capabilities": ["predict_patient_waiting_times", "identify_overcrowding_early"],
        "data_required": ["historical queue data", "appointment data", "staffing data", "arrival data"],
        "resources_required": ["existing hospital computer"],
        "constraints": [
            "budget_less_than_500_per_month",
            "no_cloud_infrastructure",
            "use_existing_hospital_computers",
            "unreliable_internet",
            "patient_data_remains_local",
            "30_day_prototype"
        ],
        "evidence_provenance": [],
        "historical_decisions": [],
        "semantic_dependencies": [
            "requires_historical_data_access",
            "requires_local_compute",
            "requires_local_dashboard"
        ],
        "architectural_decisions": {
            "compute_location": "local existing hospital computer",
            "inference_strategy": "local predictive model",
            "input_modality": "historical hospital operational data access"
        }
    }

base_arch = get_base_arch()

def make_mutation(add, remove):
    return {"add_constraints": add, "remove_constraints": remove}

def make_arch(mutations):
    arch = copy.deepcopy(base_arch)
    arch["semantic_dependencies"].extend(mutations)
    return arch

payload = {
    "project_state": {
        "user_idea": {
            "title": "Hospital Overcrowding Predictor",
            "what": "Predict patient waiting times and identify overcrowding early.",
            "why": "To manage queue times effectively.",
            "how_raw": "using existing hospital computers, historical queue, appointment, staffing and arrival data.",
            "how_structured": {}
        },
        "current_constraints": [
            "budget_less_than_500_per_month",
            "no_cloud_infrastructure",
            "use_existing_hospital_computers",
            "unreliable_internet",
            "patient_data_remains_local",
            "30_day_prototype"
        ],
        "current_requirements": [
            {"id": "req-1", "name": "Predict Wait Times", "description": "predict_patient_waiting_times", "required": True},
            {"id": "req-2", "name": "Identify Overcrowding", "description": "identify_overcrowding_early", "required": True}
        ]
    },
    "initial_architecture": base_arch,
    "candidate_uncertainties": [
        {
            "id": "unc-001",
            "question_text": "Is the historical queue, appointment, staffing, and arrival data stored in a structured, programmatically accessible format (e.g., SQL database, clean CSVs)?",
            "question_target": "Data Format and Accessibility",
            "unknown_fact": "Structured Data Availability",
            "importance": "CRITICAL",
            "yes_mutation": make_mutation(["structured_data_available"], []),
            "no_mutation": make_mutation(["unstructured_data_only"], []),
            "yes_candidate_architecture": make_arch(["requires_sql_or_csv_access"]),
            "no_candidate_architecture": make_arch(["requires_complex_scraping_or_manual_entry"])
        },
        {
            "id": "unc-002",
            "question_text": "Do the 'existing hospital computers' have reliable internal network access (LAN) to the systems holding the operational data?",
            "question_target": "Local Network (LAN) Connectivity",
            "unknown_fact": "LAN Connectivity",
            "importance": "CRITICAL",
            "yes_mutation": make_mutation(["lan_available"], []),
            "no_mutation": make_mutation(["airgapped"], []),
            "yes_candidate_architecture": make_arch(["requires_lan_access"]),
            "no_candidate_architecture": make_arch(["requires_manual_usb_transfer"])
        },
        {
            "id": "unc-003",
            "question_text": "Are we legally and administratively authorized to process patient operational data on these specific 'existing computers' without violating local privacy policies?",
            "question_target": "Legal and Privacy Authorization",
            "unknown_fact": "Local Data Processing Authorization",
            "importance": "BLOCKER",
            "yes_mutation": make_mutation(["local_processing_authorized"], []),
            "no_mutation": make_mutation(["local_processing_forbidden"], []),
            "yes_candidate_architecture": make_arch([]),
            "no_candidate_architecture": make_arch(["requires_heavy_anonymization"])
        }
    ]
}

out_file = "d:/kfiles/BlueprintAI/benchmark_suite/level6/results/v3.2_hospital_case_01/raw_refiner_output.json"
with open(out_file, "w") as f:
    json.dump(payload, f, indent=2)

print(f"Generated payload to {out_file}")
