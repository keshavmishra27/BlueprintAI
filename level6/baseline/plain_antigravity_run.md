# Run A: Baseline Evaluation

## Architecture
```json
{
  "inputs": [
    "local hospital database (historical queue, appointments, staffing)"
  ],
  "processing": [
    "Local cron job extracting data hourly",
    "Lightweight XGBoost model trained on historical data"
  ],
  "decision": [
    "Threshold-based risk alert logic (e.g. queue > 10 and staffing < 3)"
  ],
  "output": [
    "Local web dashboard accessible via hospital intranet"
  ],
  "capabilities": [
    "hourly wait time prediction",
    "overcrowding risk alerts"
  ],
  "data_required": [
    "historical queue data",
    "appointment data",
    "staffing data",
    "arrival data"
  ],
  "resources_required": [
    "existing hospital computer",
    "local Python environment"
  ],
  "constraints": [
    "budget <= $500/month",
    "no cloud infrastructure",
    "existing hospital computers only",
    "unreliable internet",
    "30-day prototype",
    "patient data must remain local"
  ],
  "evidence_provenance": [],
  "architectural_decisions": {
    "compute_location": "local existing hospital computer",
    "inference_strategy": "hourly batch prediction",
    "storage_location": "local hospital database",
    "connectivity_strategy": "local intranet only (airgapped from internet)",
    "input_modality": "database queries",
    "decision_mechanism": "XGBoost regression + rule-based thresholds",
    "human_approval": "dashboard alerts for staff review",
    "deployment_model": "local scripts via cron/task scheduler"
  }
}
```

## Python Engine Evaluation
- **Feasible**: True
- **Violations**: 0 []
- **Requirements Satisfied**: 4/4
