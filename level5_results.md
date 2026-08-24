# Level 5: Optional API / Baseline Integration Experiment (Status: Inconclusive)

> [!NOTE]
> **Status: Inconclusive (Harness Pipeline Issue)**
> In this trial run using an external local model wrapper (`qwen2.5:3b` via Ollama), the harness experienced a pipeline adaptation loop stall across all 10 scenarios (0 terminals generated, 0 candidates evaluated or rejected, 0 exhausted). This reflects a script harness communication failure rather than a deterministic engine rejection.
> 
> Core architectural validation is conducted via **Level 6 (Antigravity Agent ↔ Deterministic Engine)**.

| Metric | Baseline | BlueprintAI (Trial Run) |
|--------|---------:|------------:|
| Feasible | 2/10 | 0/10 *(Harness Pipeline Incomplete)* |

## Per-Scenario Breakdown

| Scenario | Base F | Base Reqs | Blue F | Blue Reqs | Terminals | Rejected | Exhausted | Notes |
|----------|--------|-----------|--------|-----------|-----------|----------|-----------|-------|
| 1. Hospital Waiting Time | ✓ | 0/2 | ✗ | 0 | 0 | 0 | ✗ | Loop stalled |
| 2. Crop Disease | ✗ | 0/2 | ✗ | 0 | 0 | 0 | ✗ | Loop stalled |
| 3. Personalized Learning | ✗ | 0/2 | ✗ | 0 | 0 | 0 | ✗ | Loop stalled |
| 4. Smart City Traffic | ✗ | 0/1 | ✗ | 0 | 0 | 0 | ✗ | Loop stalled |
| 5. Retail Inventory | ✓ | 0/1 | ✗ | 0 | 0 | 0 | ✗ | Loop stalled |
| 6. Remote Mining Ops | ✗ | 0/1 | ✗ | 0 | 0 | 0 | ✗ | Loop stalled |
| 7. Disaster Response | ✗ | 0/1 | ✗ | 0 | 0 | 0 | ✗ | Loop stalled |
| 8. Wearable Health | ✗ | 0/1 | ✗ | 0 | 0 | 0 | ✗ | Loop stalled |
| 9. Financial Trading | ✗ | 0/1 | ✗ | 0 | 0 | 0 | ✗ | Loop stalled |
| 10. Delivery Drones | ✗ | 0/1 | ✗ | 0 | 0 | 0 | ✗ | Loop stalled |

