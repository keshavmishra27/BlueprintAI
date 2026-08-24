# BlueprintAI Architectural Invariant

This rule defines the core structural invariant of the BlueprintAI Antigravity protocol. It must be strictly maintained in all future development.

**Gemini may propose architectures, uncertainties, evidence, mutations, and hypotheses. It may not declare feasibility, optimality, or victory. Python may evaluate, reject, rank, and select, but it may not invent architectural hypotheses.**

**The optimizer selects the best fully evaluated feasible terminal architecture discovered within the generated candidate space, regardless of whether that branch was selected by the user during exploration.**

### The Generative Layer (Antigravity/Gemini)
Responsible for:
- Generating architectural candidates
- Discovering historical evidence
- Transferring decisions
- Proposing uncertainties and branch hypotheses
- Adapting candidates to new constraints

### The Deterministic Layer (Python Engine / FastAPI)
Responsible for:
- Constraint evaluation
- Requirement evaluation
- Performance evaluation
- Cost evaluation
- Timeline evaluation
- Feasibility verification
- Branch impact calculation
- Tree state management
- Terminal state detection (Search exhaustion)
- Normalization and PathScore
- Winner selection
