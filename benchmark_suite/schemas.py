from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from decision_engine.input_layer.schemas import Requirement, ArchitectureNode
from decision_engine.tree.benchmark_evaluator import ScoringAnchors, OptimizationWeights, DeterministicEvaluationRules

class BenchmarkScenario(BaseModel):
    name: str
    description: str
    problem_what: str
    problem_why: str
    problem_how: str
    constraints: List[str]
    requirements: List[Requirement]
    scoring_anchors: ScoringAnchors
    optimization_weights: OptimizationWeights
    oracle_architecture: Optional[ArchitectureNode] = None
    
    # Internal variables for the benchmark to know hidden assumptions
    hidden_facts_to_reveal: Dict[str, str] = {}
    evaluation_rules: DeterministicEvaluationRules = DeterministicEvaluationRules()
    expected_relevant_branches: int = 0

class ExperimentManifest(BaseModel):
    model: str
    temperature: float
    scenario_version: str
    engine_version: str
    benchmark_version: str
    timestamp: str
    run_id: str
    seed: Optional[str] = None
    scenario_rule_hashes: Dict[str, str] = {}

class GenerationLog(BaseModel):
    run_id: str
    scenario_id: str
    arm: str
    generation_id: str
    parent_node_id: Optional[str] = None
    model: str
    prompt_hash: str
    response_hash: Optional[str] = None
    raw_response: str
    attempt: int = 1
    result: str = "VALID" # VALID, INVALID_JSON, GENERATION_FAILURE
    latency_ms: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

class BenchmarkMetrics(BaseModel):
    run_id: str
    arm: str
    feasibility: bool
    requirements_met: int
    oracle_hit: bool
    oracle_gap: float
    delta_f: float
    uar: float
    questions_asked: int
    irrelevant_questions: int
    exploration_efficiency: float
    terminal_candidates: int
    unselected_winner: bool
    decision_regret: float
    termination_status: str
    initial_cgfr: float
    recovery_rate: float
    final_cgfr: float
    protocol_cost_gemini_calls: int
    protocol_cost_input_tokens: int
    protocol_cost_output_tokens: int
    protocol_cost_total_tokens: int
    protocol_cost_latency_ms: float
    her: float = 0.0
    bgr: float = 0.0
