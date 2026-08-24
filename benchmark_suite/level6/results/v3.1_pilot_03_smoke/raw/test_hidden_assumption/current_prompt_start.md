# RUN: v3.1_pilot_03_smoke | SCENARIO: test_hidden_assumption | STEP: 0
# INVOCATION: 1900d02f-cc1a-4f9a-ba86-32b58049b4e2

# SCENARIO: test_hidden_assumption
Problem: Predict patient waiting times and identify overcrowding.
Why: Hospitals need earlier intervention without expensive infrastructure.
How: AI-based prediction using historical queue, appointment, staffing and arrival data.
Constraints:
  - budget <= $500/month
  - no cloud infrastructure
  - existing hospital computers only
  - unreliable internet
  - 30-day prototype
  - patient data must remain local
Requirements:
  - predict waiting time
  - identify overcrowding risk
  - useful accuracy
  - low operating cost
