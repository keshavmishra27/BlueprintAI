# RUN: v3.1_pilot_03 | SCENARIO: test_hidden_assumption | STEP: 0
# INVOCATION: c5f16d7b-0c79-471b-90cf-cf2f4da55c0e

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
