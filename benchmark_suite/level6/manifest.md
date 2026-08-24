LEVEL 6 EXPERIMENT MANIFEST

Engine:
  evaluator_hash: 776D1543E5D4267A006A9B93479F64AD72A09ED3489DB307DAD56682EEE07929
  evaluator_input_hash: 575606BC3727CB938D3E512FDFEC3145B1F3E170B616B4EEE1ACCBBB8345E8EE
  optimizer_hash: ACFCA93CD02ABD5DF465410D2455AE0C31CE7F03DD9D2C7804847E1C7BCCAA07
  protocol_hash: 4B9F2FD3999AF6673C4F7F4D3124FDE2E7E3A4C3C9A285D4A77B6A701AA52CE6

Runtime:
  IDE: Antigravity
  Agent runtime: Antigravity IDE Agent (Gemini-2.5-Pro equivalent via IDE interface)

Information:
  Public scenario: FROZEN (Hash: E8EBD908D3B6E3F1C3C082BF3C4DCBFDB41B39EB58A5A6C7BB45949FD5AFC1D8)
  Hidden user policy: FROZEN
  Oracle: FROZEN

Baseline:
  Single-shot architecture
  No uncertainty exploration
  Evaluation via identical `/api/journey/evaluate` endpoint

BlueprintAI:
  Architecture + uncertainty generation
  Python uncertainty selection via `/api/journey/start`
  Frozen user-policy answers provided interactively
  Branch generation via `/api/journey/answer`
  Global terminal optimization

Stopping Conditions (driven by deterministic engine):
  BEST_ARCHITECTURE_FOUND
  NO_FEASIBLE_ARCHITECTURE_FOUND
  NO_OPTIMIZABLE_ARCHITECTURE_NEEDS_INFORMATION

Mutation policy:
  NO ENGINE MODIFICATIONS DURING BENCHMARK
  NO SCENARIO MODIFICATIONS DURING BENCHMARK
