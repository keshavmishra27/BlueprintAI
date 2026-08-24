# Level 6 Benchmark Protocol: Antigravity Agent Runtime

This document formally defines the Level 6 experiment protocol. It specifies exactly how the IDE generative agent (Antigravity) must interact with the deterministic Python engine (BlueprintAI) and the Benchmark Controller.

## Authority Boundaries

**Agent:**
- Generates architectures.
- Generates uncertainties based on the public scenario.
- Generates branch hypotheses upon receiving user policy answers.
- Adapts architectures after answers.
- **Does not** evaluate feasibility itself.
- **Does not** select the mathematical winner.

**Python Engine (FastAPI Backend):**
- Evaluates architectures.
- Evaluates branch consequences.
- Selects the highest-impact uncertainty.
- Maintains decision-tree state.
- Determines terminal states.
- Computes the optimization.
- Selects `best_path_id`.

**Benchmark Controller:**
- Supplies the public scenario (Constraints, Requirements).
- **Maintains hidden user facts.**
- Answers selected questions according to a frozen policy.
- Records the experiment results.
- **Must not** generate or modify architectures itself.

---

## Benchmark Execution Paths

The experiment consists of two arms run against the same scenario:

### 1. Baseline (Single-Shot)

The baseline must remain completely tree-free. It generates a single architecture and stops.

1. **Controller** provides Public Scenario + Known Constraints + Known Requirements.
2. **Agent** generates ONE architecture.
3. **Agent** posts to engine:
   ```http
   POST /api/evaluate
   ```
4. **Python** scores it.
5. **Controller** records result. Done.

*Note: The Baseline must not generate uncertainties, ask questions, or call journey start/answer endpoints.*

### 2. BlueprintAI (Exploration Tree)

Only the BlueprintAI arm is permitted to explore unknowns.

1. **Controller** provides exactly the same Public Scenario.
2. **Agent** generates initial Architecture + Uncertainties.
3. **Agent** posts to engine:
   ```http
   POST /api/journey/start
   ```
4. **Python** selects an uncertainty and returns the question.
5. **Agent** asks the Controller.
6. **Controller** resolves the question against its hidden policy and returns the answer.
7. **Agent** generates the adapted branch hypothesis.
8. **Agent** posts the branch:
   ```http
   POST /api/journey/answer
   ```
9. **Python** evaluates the consequence. If Python reports `UNEXPLORED_HYPOTHESIS`, the Agent generates the corresponding alternative.
10. **Python** eventually calculates the tree is resolved and assembles the Pareto front.
11. **Python** returns `BEST_ARCHITECTURE_FOUND`.
12. **Controller** records result. Done.
