# BlueprintAI

> **"The LLM proposes. The Decision Engine decides."**

BlueprintAI is an AI-assisted software architecture and idea refinement platform where generative AI hypotheses are evaluated, pruned, and refined through a **deterministic decision graph, epistemic constraints, and branch-local evidence**.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/pytest-Passing-success)](tests/)
[![Governance](https://img.shields.io/badge/Decision%20Engine-Deterministic%20Governance-purple)](decision_engine/)

---

## 1. What is BlueprintAI?

Most AI "architecture generators" suffer from **architectural laundering**: an LLM assumes a technology stack (e.g., Kafka, Microservices, Cloud Vector DB) and hallucinates requirements to justify it. When given multiple architectures or varying prompts, standard LLM wrappers choose winners based on persuasive prose, prompt order, or token biases.

BlueprintAI fundamentally splits this responsibility, offering a modular suite of tools that separates generative proposals from deterministic governance.

```text
BlueprintAI
│
├── Idea Refiner (idea_refiner/)
│   └── Turns messy natural-language ideas into governed architectures
│
├── Decision Engine (decision_engine/)
│   └── Deterministically evaluates candidates, checks constraints, and scores paths
│
├── Repo Judge (repo_checker/)
│   └── Evaluates local repositories against security, quality, and architecture invariants
│
└── Project Suggester (.agents/skills/project-suggest/)
    └── Analyzes developer profiles to suggest optimal resume/hackathon projects
```

---

## 2. Core Architecture: The LLM vs. Decision Engine Boundary

The core of BlueprintAI rests on a strict boundary between what the LLM is allowed to do and what the Python backend does.

```text
                  ┌────────────────────────────────────────┐
                  │              LLM / Proposer            │
                  │  - Extracts requirements & provenance  │
                  │  - Proposes candidate architectures    │
                  │  - Surfaces epistemic uncertainties    │
                  │  - Generates questions & explanations  │
                  └───────────────────┬────────────────────┘
                                      │ Hypotheses
                                      ▼
                  ┌────────────────────────────────────────┐
                  │        Decision Engine / Graph         │
                  │  - Enforces epistemic boundary         │
                  │  - Validates semantic dependencies     │
                  │  - Executes hard gating (feasibility)  │
                  │  - Evaluates Pareto frontier           │
                  │  - Computes deterministic PathScore    │
                  └───────────────────┬────────────────────┘
                                      │ argmax Score
                                      ▼
                  ┌────────────────────────────────────────┐
                  │       Winning Governed Architecture    │
                  └────────────────────────────────────────┘
```

BlueprintAI guarantees four core deterministic invariants:

| Invariant | System Guarantee |
|---|---|
| **Candidate Order Invariance** | Permuting candidate architectures (`[A, B, C]`, `[C, A, B]`, `[B, C, A]`) produces the **exact same winning architecture and score**. |
| **Narrative / Hype Resistance** | Flamboyant LLM prose (*"THIS IS A REVOLUTIONARY BEST-IN-CLASS STACK"*) has **zero mathematical effect** on the decision score. |
| **Epistemic Hard Gating** | Candidates with unsatisfied dependencies (e.g., requiring continuous internet in an offline environment) are strictly **REJECTED**, never hand-waved away. |
| **Tamper-Evident Provenance** | Every decision produces immutable SHA-256 fingerprints guaranteeing reproducible auditability. |

---

## 3. Individual Components & Skills

BlueprintAI is composed of specialized skills and engines. For detailed specifications and canonical output examples, see the individual component documentation:

- **[Idea Refiner Documentation](idea_refiner/README.md)**: Details on the 6-stage refinement pipeline, epistemic requirement extraction, and a complete canonical walkthrough of how a messy idea becomes a governed architecture.
- **[Decision Engine](decision_engine/)**: The deterministic graph arbiter enforcing epistemic boundaries and robustness scenarios.
- **[Knowledge Base](knowledge_base/)**: Curated benchmark evidence, SIH winners, and historical architectural patterns used to ground LLM hypotheses.

---

## 4. Repository Structure

```text
BlueprintAI/
├── README.md                    ← You are here (System Overview)
│
├── decision_engine/             ← The Deterministic Arbiter
│   ├── tree/                    # Graph, Tree State, Optimizer, Fingerprinting
│   ├── input_layer/             # Schemas, Hard Gates, Ontology, Evaluator
│   └── governance/              # Policy engine, Robustness scenarios
│
├── idea_refiner/                ← Generative Proposal & Presentation Layer
│   ├── README.md                # Idea Refiner Product Specification & Output Walkthrough
│   ├── SKILL.md                 # Agent Operational Contract
│   ├── orchestrator.py          # End-to-end pipeline coordination
│   └── parsers/                 # Requirement Extractor & Epistemic Parsers
│
├── .agents/skills/              ← Agent Skill Contracts
│   ├── idea-refiner/
│   ├── repo-judge/
│   └── project-suggest/
│
└── tests/                       ← Deterministic test suites
    ├── test_decision_engine.py
    └── test_idearefiner_governance.py
```

---

## 5. Milestone Progression

| Milestone | Scope | Status |
|---|---|:---:|
| **M1 – M8** | Core Decision Tree, Graph Representation, Hard Gates, Pareto Optimization | ✅ Complete |
| **M9 – M10** | Epistemic Provenance Boundary & Canonical Hashing | ✅ Complete |
| **M11 – M12** | Future Scenario Robustness, Policy Evaluation & Governance API | ✅ Complete |
| **M13-A** | Deterministic Black-Box Acceptance Test | ✅ Complete |
| **M13-B** | Decision Engine Governance & Invariance Proof Test | ✅ Complete |
| **M13-C** | Live Interactive Human + Multi-Turn Idea Refinement | 🔄 Next |
| **M14+** | Full Web UI & Production API Service | 📋 Planned |

---

## 6. Running Tests & Governance Proof

To run the deterministic governance acceptance suite (proving candidate-order invariance, narrative-hype resistance, and epistemic hard gating):

```bash
# Run the M13-B governance proof test suite
pytest tests/test_idearefiner_governance.py -v

# Run the complete decision engine test suite
pytest tests/test_decision_engine.py -v

# Run the standalone visual governance demonstration
python verify_governance_proof.py
```
