from typing import List, Tuple
from .schemas import ArchitectureNode, Requirement, ArchitectureComparison, RequirementEvaluation, Winner, CandidateStatus, EvalStatus, DimensionEvaluation

def evaluate_requirements(arch: ArchitectureNode, env_requirements: List[Requirement]) -> List[bool]:
    results = []
    arch_caps = [cap.lower() for cap in arch.capabilities]
    
    for req in env_requirements:
        req_name = req.name.lower()
        if "attendance" in req_name:
            if any("attendance" in cap or "presence detection" in cap or "qr code" in cap or "face recognition" in cap or "biometric" in cap for cap in arch_caps):
                results.append(True)
            else:
                results.append(False)
        elif "struggling" in req_name or "knowledge tracing" in req_name:
            if any("knowledge tracing" in cap or "weakness detection" in cap or "personalized recommendation" in cap or "analytics" in cap or "student analysis" in cap or "struggling student detection" in cap or "weak-topic detection" in cap for cap in arch_caps):
                results.append(True)
            else:
                results.append(False)
        elif "doubts" in req_name:
            if any("llm" in cap or "generative qa" in cap or "doubt resolution" in cap or "answer arbitrary doubts" in cap for cap in arch_caps):
                results.append(True)
            else:
                results.append(False)
        elif "detect objects" in req_name or "video analysis" in req_name:
            if "prerecorded" in " ".join(arch.data_required).lower() and "immediately" in req_name:
                results.append(False)
            elif any("object detection" in cap or "computer vision" in cap for cap in arch_caps):
                results.append(True)
            else:
                results.append(False)
        elif "predict waiting time" in req_name:
            if any("predict" in cap or "wait time" in cap or "forecasting" in cap for cap in arch_caps):
                results.append(True)
            else:
                results.append(False)
        elif "identify overcrowding risk" in req_name:
            if any("overcrowd" in cap or "risk" in cap or "alert" in cap for cap in arch_caps):
                results.append(True)
            else:
                results.append(False)
        elif "useful accuracy" in req_name:
            # We assume any ML/statistical model gives some accuracy, so we check for ML/model presence
            if "ml" in " ".join(arch.processing).lower() or "model" in " ".join(arch.processing).lower() or "xgboost" in " ".join(arch.processing).lower():
                results.append(True)
            else:
                results.append(False)
        elif "low operating cost" in req_name:
            # Check if it doesn't require cloud or paid APIs
            if any("cloud" in res.lower() or "paid" in res.lower() for res in arch.resources_required):
                results.append(False)
            else:
                results.append(True)
        else:
            results.append(False)
            
    return results

def get_requirement_reason(arch_name: str, req: Requirement, satisfied: bool) -> str:
    if satisfied:
        return f"{arch_name} capabilities directly address '{req.name}'."
    return f"{arch_name} capabilities lack explicit mechanisms for '{req.name}'."

def check_violations(arch: ArchitectureNode, env_constraints: List[str]) -> List[str]:
    violations = []
    for constraint in env_constraints:
        c_lower = constraint.lower()
        if c_lower == "no_gpu":
            for res in arch.resources_required:
                if "gpu" in res.lower():
                    violations.append(f"Requires '{res}' which violates constraint '{constraint}'.")
        elif c_lower == "no_historical_data" or c_lower == "missing historical data":
            for data in arch.data_required:
                if "historical" in data.lower():
                    violations.append(f"Requires '{data}' which violates constraint '{constraint}'.")
        elif c_lower == "no_cloud" or c_lower == "offline" or "no cloud" in c_lower:
            for res in arch.resources_required:
                if "cloud" in res.lower() or "internet" in res.lower() or "external api" in res.lower():
                    violations.append(f"Requires '{res}' which violates constraint '{constraint}'.")
        elif c_lower == "no_external_storage" or "patient data must remain local" in c_lower:
            for res in arch.resources_required:
                if "external storage" in res.lower() or "cloud database" in res.lower() or "centralized storage" in res.lower():
                    violations.append(f"Requires '{res}' which violates constraint '{constraint}'.")
        elif c_lower == "limited_bandwidth" or "low bandwidth" in c_lower:
            for data in arch.data_required:
                if "live video stream" in data.lower() or "high bandwidth" in data.lower():
                    violations.append(f"Requires '{data}' which violates constraint '{constraint}'.")
        elif c_lower == "human_approval_required":
            caps = [cap.lower() for cap in arch.capabilities]
            if any("autonomous" in cap or "automatic routing without approval" in cap for cap in caps):
                violations.append(f"Capability violates constraint '{constraint}'.")
        elif "48-hour prototype" in c_lower or "24-hour prototype" in c_lower:
            if "custom_hardware" in arch.semantic_dependencies or "massive_data_collection" in arch.semantic_dependencies:
                violations.append(f"Requires custom hardware or massive data which violates constraint '{constraint}'.")
        elif "no_paid_apis" in c_lower or "no paid apis" in c_lower:
            if "paid_api" in arch.semantic_dependencies or "commercial_cloud" in arch.semantic_dependencies:
                violations.append(f"Requires paid APIs which violates constraint '{constraint}'.")
        elif "very small budget" in c_lower or "budget" in c_lower:
            if "paid_api" in arch.semantic_dependencies or "commercial_cloud" in arch.semantic_dependencies:
                violations.append(f"Requires paid APIs/cloud which violates constraint '{constraint}'.")
        elif "internet is unreliable" in c_lower or "poor connectivity" in c_lower or "unreliable internet" in c_lower:
            if "requires_continuous_connectivity" in arch.semantic_dependencies or "continuous_streaming" in arch.semantic_dependencies:
                violations.append(f"Requires continuous internet which violates constraint '{constraint}'.")
            elif "requires_cloud" in arch.semantic_dependencies:
                violations.append(f"Requires cloud computing which violates constraint '{constraint}'.")
        elif "cannot store sensitive student data externally" in c_lower or "student data must remain local" in c_lower:
            if "external_storage" in arch.semantic_dependencies or "external_data_transfer" in arch.semantic_dependencies:
                violations.append(f"Requires external storage/transfer which violates constraint '{constraint}'.")
        elif "teachers must approve important actions" in c_lower or "teacher approval required" in c_lower:
            if "requires_automatic_action" in arch.semantic_dependencies or "autonomous_actions" in arch.semantic_dependencies:
                violations.append(f"Requires autonomous action which violates constraint '{constraint}'.")
        elif "existing college computers are basic" in c_lower or "basic cpu computers" in c_lower or "existing hospital computers only" in c_lower:
            if "requires_gpu" in arch.semantic_dependencies or "requires_edge_gpu" in arch.semantic_dependencies or "local_gpu_required" in arch.semantic_dependencies:
                violations.append(f"Requires GPU which violates constraint '{constraint}'.")
        elif "prototype needed in 7 days" in c_lower or "7-day prototype" in c_lower or "30-day prototype" in c_lower:
            if "custom_hardware" in arch.semantic_dependencies:
                violations.append(f"Requires custom hardware which violates constraint '{constraint}'.")
        
        if "no direct db connection" in c_lower:
            uses_db = any("database" in d.lower() or "db" in d.lower() for k, d in arch.architectural_decisions.items()) or \
                      any("database" in p.lower() for p in (arch.inputs + arch.processing + arch.decision + arch.output))
            if uses_db:
                violations.append("Architecture requires direct database connection, which is prohibited.")
                
        if "budget <= $1/" in c_lower or "latency <= 1ms" in c_lower:
            violations.append(f"Impossible constraint '{constraint}' cannot be met by any architecture.")

    return violations

from decision_engine.input_layer.ontology import evaluate_ontology

def evaluate_dimensions(arch: ArchitectureNode, env_constraints: List[str], env_requirements: List[Requirement]) -> Tuple[DimensionEvaluation, List[str], List[bool]]:
    dims = DimensionEvaluation(
        constraint=EvalStatus.PASS,
        requirement=EvalStatus.PASS,
        performance=EvalStatus.UNKNOWN,
        cost=EvalStatus.UNKNOWN,
        timeline=EvalStatus.UNKNOWN
    )
    
    violations = []
    
    if arch.candidate_status == CandidateStatus.NO_CANDIDATE:
        dims.constraint = EvalStatus.FAIL
        dims.requirement = EvalStatus.FAIL
        dims.performance = EvalStatus.FAIL
        dims.cost = EvalStatus.FAIL
        dims.timeline = EvalStatus.FAIL
        return dims, ["NO CANDIDATE"], [False]*len(env_requirements)
        
    combined_constraints = list(set(env_constraints + arch.constraints))
    violations = check_violations(arch, combined_constraints)
    
    # Ontology evaluation
    ontology_res = evaluate_ontology(arch, combined_constraints, env_requirements)
    violations.extend(ontology_res.constraint_failures)
    
    dims.constraint = EvalStatus.FAIL if violations else EvalStatus.PASS
    
    req_results = evaluate_requirements(arch, env_requirements)
    
    # Ontology can fail specific requirements
    for idx, req in enumerate(env_requirements):
        if req.name in ontology_res.requirement_failures:
            req_results[idx] = False
            
    reqs_met = sum(1 for sat in req_results if sat)
    dims.requirement = EvalStatus.PASS if reqs_met == len(env_requirements) else EvalStatus.FAIL
    
    if arch.performance:
        est = arch.performance.get('estimated_latency_ms')
        limit = arch.performance.get('latency_limit_ms')
        if est is not None and limit is not None:
            dims.performance = EvalStatus.FAIL if est > limit else EvalStatus.PASS
        else:
            dims.performance = EvalStatus.UNKNOWN
    else:
        dims.performance = EvalStatus.UNKNOWN
        
    if arch.cost:
        est = arch.cost.get('estimated_monthly_cost')
        limit = arch.cost.get('budget_limit')
        if est is not None and limit is not None:
            dims.cost = EvalStatus.FAIL if est > limit else EvalStatus.PASS
        else:
            dims.cost = EvalStatus.UNKNOWN
    else:
        dims.cost = EvalStatus.UNKNOWN
        
    if arch.timeline:
        est = arch.timeline.get('estimated_days')
        limit = arch.timeline.get('deadline_days')
        if est is not None and limit is not None:
            dims.timeline = EvalStatus.FAIL if est > limit else EvalStatus.PASS
        else:
            dims.timeline = EvalStatus.UNKNOWN
    else:
        if "massive_custom_engineering" in arch.semantic_dependencies and any("7-day" in c.lower() for c in env_constraints):
            dims.timeline = EvalStatus.FAIL
        else:
            dims.timeline = EvalStatus.UNKNOWN
            
    return dims, violations, req_results

def evaluate_battle(
    user_arch: ArchitectureNode, 
    player_b_arch: ArchitectureNode, 
    env_constraints: List[str], 
    env_requirements: List[Requirement]
) -> ArchitectureComparison:
    a_dims, a_violations, a_req_results = evaluate_dimensions(user_arch, env_constraints, env_requirements)
    b_dims, b_violations, b_req_results = evaluate_dimensions(player_b_arch, env_constraints, env_requirements)
    
    req_evaluations = []
    for i, req in enumerate(env_requirements):
        a_sat = a_req_results[i]
        b_sat = b_req_results[i]
        req_evaluations.append(
            RequirementEvaluation(
                requirement=req.name,
                user_satisfies=a_sat,
                player_b_satisfies=b_sat,
                user_reason=get_requirement_reason("User", req, a_sat),
                player_b_reason=get_requirement_reason("Player B", req, b_sat)
            )
        )
        
    def passes_hard_gates(dims: DimensionEvaluation) -> bool:
        return dims.constraint == EvalStatus.PASS and dims.requirement == EvalStatus.PASS and dims.performance != EvalStatus.FAIL and dims.cost != EvalStatus.FAIL and dims.timeline != EvalStatus.FAIL
        
    a_valid = passes_hard_gates(a_dims)
    b_valid = passes_hard_gates(b_dims)

    winner = Winner.TIE
    reasoning = ""
    
    if a_valid and not b_valid:
        winner = Winner.USER
        reasoning = "Player B's architecture is invalid (fails a hard gate). User architecture survives."
    elif b_valid and not a_valid:
        winner = Winner.PLAYER_B
        reasoning = "User architecture is invalid (fails a hard gate). Player B wins."
    elif not a_valid and not b_valid:
        winner = Winner.TIE
        reasoning = "Both architectures are invalid (fail hard gates)."
    else:
        winner = Winner.TIE
        reasoning = "Both are feasible and pass all hard gates."

    return ArchitectureComparison(
        b_feasible=b_valid,
        a_feasible=a_valid,
        b_reqs_satisfied=b_dims.requirement == EvalStatus.PASS,
        a_reqs_satisfied=a_dims.requirement == EvalStatus.PASS,
        b_constraint_violations=b_violations,
        a_constraint_violations=a_violations,
        requirement_evaluations=req_evaluations,
        b_dimensions=b_dims,
        a_dimensions=a_dims,
        winner=winner,
        reasoning=reasoning
    )
