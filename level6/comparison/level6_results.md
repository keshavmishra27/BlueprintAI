# Level 6 Experiment Results

This document compares the Baseline run (single-shot Antigravity architecture) with the BlueprintAI protocol run, utilizing the deterministic Python evaluator.

## 1. Experimental Setup

- **Scenario:** Predict patient waiting times to identify overcrowding.
- **Constraints:** Budget <= $500/mo, no cloud, existing hospital computers only, unreliable internet, 30-day prototype, local patient data.
- **Requirements:** Predict wait time, identify overcrowding risk, useful accuracy, low operating cost.
- **Agent Runtime:** Antigravity (Live Execution)
- **Evaluator:** Python Deterministic Engine

## 2. The Baseline (Run A)

In the single-shot run, Antigravity produced the following architecture:
- **Core Processing:** Local cron job extracting data hourly to a local XGBoost model.
- **Data Access:** Direct queries to the local hospital database.

**Evaluation:**
- **Constraint Feasibility:** Pass
- **Requirements Satisfied:** 4/4
- **Within-run PathScore:** -5.0
- **Candidates Explored:** 1
- **Terminal Candidates (F):** 1

## 3. The BlueprintAI Protocol (Run B)

In this run, Antigravity was required to generate uncertainties alongside the architecture.
- **Python Engine** evaluated the uncertainties deterministically and selected the highest-impact question: *"Do the existing hospital computers have permission to query the central hospital database directly?"*
- **The User** revealed a hidden constraint by answering **NO**.
- **Antigravity** adapted the architecture for the NO branch (using a daily CSV export via USB).
- **Python Engine** recognized an `UNEXPLORED_HYPOTHESIS` (the YES branch) and forced evaluation to ensure space exhaustion.

**Evaluation:**
- **Constraint Feasibility:** Pass
- **Requirements Satisfied:** 4/4
- **Within-run PathScore:** 0.55
- **Candidates Explored:** 2
- **Terminal Candidates (F):** 2
- **Critical Assumptions Identified:** 1
- **Critical Assumptions Resolved:** 1
- **Selected Architecture:** Adapted (CSV Export)
- **Was optimal branch selected conversationally?** Yes (User selected NO branch).

## 4. Comparison Metrics

| Metric | Plain Gemini (Baseline) | BlueprintAI + Gemini |
| :--- | :--- | :--- |
| **Candidates Explored** | 1 | 2 |
| **Requirements Satisfied** | 4/4 | 4/4 |
| **Known Constraints Passed** | ✓ | ✓ |
| **Critical Assumptions Identified** | 0 | 1 |
| **Critical Assumptions Resolved** | 0 | 1 |
| **Terminal Candidates (F)** | 1 | 2 |
| **Best Architecture Selected** | Baseline (Direct DB query) | Adapted (CSV Dump via USB) |

### Delta Analysis

- $\Delta F = 2 - 1 = +1$ (Candidate space expanded)
- $\Delta R = 4 - 4 = 0$ (Both satisfied all requirements)
- $\Delta \text{UAR} = 1 - 0 = +1$ (Unverified Assumption Resolution)

*Note: PathScore is a comparative ranking within the current explored candidate set, not an absolute architecture-quality score. Since the two runs had different terminal candidate sets ($C_{max}^{baseline} \neq C_{max}^{BlueprintAI}$), their internal PathScores are not directly comparable. A common-reference architecture score would be required for absolute comparison.*

## 5. Conclusion: Proof of Concept

**Level 6 demonstrates the core BlueprintAI mechanism.**

The single-shot Antigravity architecture satisfied all explicitly known constraints and requirements, but depended on an unverified assumption about direct hospital database access. Because the Baseline run operates single-shot, it would have resulted in deploying an architecture that would require redesign before deployment because its database-access assumption was invalid.

The BlueprintAI protocol generated an uncertainty targeting that assumption. Python deterministically selected it as high-impact, and the user resolved the uncertainty by stating that direct access was prohibited. Antigravity then generated an alternative architecture using an authorized CSV/USB data-transfer mechanism.

The deterministic engine retained the original hypothesis as an alternative, evaluated both terminal candidates, and selected the mathematical winner according to its configured objective. In this experiment, the mathematical winner happened to coincide with the user's selected branch.

Therefore, this experiment demonstrates that the BlueprintAI protocol can **expand the candidate space and explicitly resolve hidden architectural assumptions that a single-shot architecture may leave implicit**.

This is evidence supporting the "Gemini explores, Python evaluates and optimizes" architecture. It is not, by itself, statistical proof that BlueprintAI consistently outperforms single-shot Gemini. That requires repeated controlled experiments across diverse scenarios.
