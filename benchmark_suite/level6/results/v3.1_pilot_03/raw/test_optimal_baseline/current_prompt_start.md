# RUN: v3.1_pilot_03 | SCENARIO: test_optimal_baseline | STEP: 0
# INVOCATION: 6151f0a8-08cd-4e84-9eaa-5ba14a43e824

# SCENARIO: test_optimal_baseline
Problem: Dashboard
Why: Need to see data
How: Query DB
Constraints:
  - budget <= $1000/month
  - reliable internet
Requirements:
  - fast query
