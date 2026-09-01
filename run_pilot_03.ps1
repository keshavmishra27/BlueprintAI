$env:BLUEPRINT_SMOKE_TEST = "0"

$env:BLUEPRINT_RUN_ID = "v3.1_pilot_03"

$env:BLUEPRINT_STEP_TIMEOUT = "300.0"

. .\venv\Scripts\Activate.ps1

python benchmark_suite\level6\agent_driver.py

