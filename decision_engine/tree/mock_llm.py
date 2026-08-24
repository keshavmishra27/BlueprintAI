import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.tree.tree_schemas import ArchitectureState, ProjectState
from decision_engine.input_layer.schemas import ArchitectureNode

def simulate_player_b_generation(v_num: int, project_state: ProjectState) -> ArchitectureState:
    """
    Simulates Player B adapting to constraints.
    In the real engine, this passes project_state to the LLM to generate the ArchitectureNode.
    """
    arch = ArchitectureNode(
        inputs=["Patient demand", "Hospital resource state"],
        processing=["Demand prediction", "Bottleneck prediction", "Cloud inference", "GPU acceleration"],
        decision=["Proactive resource allocation"],
        output=["Dynamic patient routing"],
        data_required=["Historical patient arrival data", "Real-time hospital resource data"],
        resources_required=["ML model", "Hospital database", "Prediction service", "Cloud Infrastructure", "GPU instance"],
        constraints=["Requires reliable operational data"],
        capabilities=["demand prediction", "bottleneck prediction", "proactive routing", "cloud-scale processing", "gpu-accelerated learning"]
    )
    
    based_on = None
    
    # Adapt to constraints
    env_str = " ".join(project_state.current_constraints).lower()
    
    # Simple mocked adaptation rules based on constraints
    if "no historical data" in env_str:
        arch.processing = ["Real-time queue monitoring"]
        arch.decision = ["Rule-based bottleneck detection"]
        arch.data_required = ["Real-time hospital resource data"]
        arch.capabilities = ["rule-based routing", "live bottleneck detection"]
        arch.resources_required = ["Local database", "Rules Engine"]
        if "no cloud infrastructure" not in env_str:
            arch.resources_required.append("Cloud Infrastructure")
            arch.capabilities.append("cloud-scale processing")
        based_on = "Switched from ML to Rule-based due to 'no historical data' constraint."
    elif "no gpu instance" in env_str:
        arch.processing = ["Demand prediction", "CPU-based prediction", "Cloud inference"]
        arch.resources_required = [r for r in arch.resources_required if "GPU" not in r]
        arch.capabilities = [c for c in arch.capabilities if "gpu" not in c]
        based_on = "Switched to CPU-based inference due to 'no GPU instance' constraint."
    elif "no cloud infrastructure" in env_str:
        arch.processing = ["Local Edge Inference", "Bottleneck prediction"]
        arch.resources_required = [r for r in arch.resources_required if "Cloud" not in r]
        arch.resources_required.append("Local Edge Server")
        arch.capabilities = [c for c in arch.capabilities if "cloud" not in c]
        arch.capabilities.append("edge computing")
        based_on = "Switched to edge inference due to 'no cloud infrastructure' constraint."
        
    return ArchitectureState(
        architecture=arch,
        generation=v_num,
        based_on=based_on
    )
