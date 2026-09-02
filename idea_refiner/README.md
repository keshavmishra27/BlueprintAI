# Idea Refiner

The Idea Refiner (`/idearefiner`) is the conversational interface and interpretation layer for BlueprintAI. It transforms a user's messy, unstructured ideas into typed requirements and candidate architectures, which are then evaluated and strictly governed by the underlying **Decision Engine**.

## What a user experiences

The interactive session progresses through the following strict pipeline:

1. **Raw Idea**: The user provides a messy idea (e.g., "I want an app for students to upload PDFs...").
2. **Requirements**: The `RequirementExtractor` uses an LLM to pull structured functional/non-functional requirements from the idea.
3. **Candidate Architectures**: The LLM proposes candidate technical architectures to fulfill those requirements.
4. **Uncertainty**: The **Decision Engine** evaluates the candidates and identifies an `UNRESOLVED` state. A separate generator translates this state into a human-facing question.
5. **Human Answer**: The human provides a messy answer (e.g., "No, most have cheap phones").
6. **Epistemic Resolution**: The `EpistemicResolver` interprets the answer and maps it to a proposed, typed ontology value (e.g., `student_hardware=low_end`).
7. **Decision Graph**: The **Decision Engine** validates the proposed resolution against the active uncertainty and ontology, and creates a branch-local state transition containing the new evidence.
8. **Best Architecture**: The **Decision Engine's optimizer** mathematically determines the argmax winner across the newly evaluated branches.
9. **Audit Trace**: A tamper-evident trace is output, proving why the architecture won based strictly on properties and constraints.

## The Core Boundary (Constitution of Idea Refiner)

The most critical architectural guarantee of the Idea Refiner is:

> **The LLM proposes. The human provides evidence. The Decision Engine decides.**

This hierarchy is absolute:

```text
┌──────────────────────────────────────────────┐
│                  HUMAN                       │
│                                              │
│  messy idea / answer / clarification         │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│                    LLM                       │
│                                              │
│  proposes requirements                       │
│  proposes architectures                      │
│  interprets human answers                    │
│  proposes epistemic mappings                 │
│                                              │
│              NO DECISION AUTHORITY           │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│             EPISTEMIC RESOLVER               │
│                                              │
│  converts interpretation → typed proposal    │
│                                              │
│              NO DECISION AUTHORITY           │
└──────────────────────┬───────────────────────┘
                       ↓
┌══════════════════════════════════════════════┐
║              DECISION ENGINE                 ║
║                                              ║
║  ontology validation                         ║
║  uncertainty validation                      ║
║  branch creation                             ║
║  constraint evaluation                       ║
║  hard gating                                 ║
║  feasibility                                 ║
║  scoring                                     ║
║  optimization                                ║
║  winner selection                            ║
║                                              ║
║              DECISION AUTHORITY              ║
╚══════════════════════╤═══════════════════════╝
                       ↓
                BEST ARCHITECTURE
                       +
                 DECISION TRACE
```

### M13-C0: Interactive Engine Harness

The interactive harness demonstrates this boundary. When a user answers an epistemic question, the resolution mutates the graph, but the LLM and the user have no authority over scoring or architecture selection. 

**Example Governance Proof:**
```text
========================================================
DECISION ENGINE GOVERNANCE PROOF
========================================================

Human input:
"Most students have low-end phones."

Epistemic target:
student_hardware

Engine Validation:
VALID (Ontology match confirmed)
Branch Derived: cand_c_branch_student_hardware_low_end

--------------------------------------------------------
CAND_A
--------------------------------------------------------
requires_continuous_connectivity
basic_mobile_hardware
-> REJECTED

--------------------------------------------------------
CAND_B
--------------------------------------------------------
high_end_hardware
basic_mobile_hardware
-> REJECTED

--------------------------------------------------------
CAND_C
--------------------------------------------------------
basic_mobile_hardware
blob_storage
basic_mobile_hardware
-> FEASIBLE

PathScore:
WINNER = 79.5

--------------------------------------------------------
WINNER
--------------------------------------------------------
cand_c_branch_student_hardware_low_end

Selection mechanism: Decision Graph optimizer
LLM-selected winner: NONE
User-selected winner: NONE
Narrative influence: NONE

========================================================
VERDICT: GRAPH SELECTED THE ARCHITECTURE
========================================================
```
