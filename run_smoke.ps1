$env:BLUEPRINT_SMOKE_TEST="1"

$env:BLUEPRINT_RUN_ID = "v3.1_pilot_03_smoke_qualified_v2"

$env:BLUEPRINT_STEP_TIMEOUT="300.0"

. .\venv\Scripts\Activate.ps1

python benchmark_suite\level6\agent_driver.py

