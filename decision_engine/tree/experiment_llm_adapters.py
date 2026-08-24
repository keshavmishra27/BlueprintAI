import json
from typing import List, Optional
from pydantic import BaseModel
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from backend.app.services.llm_factory import invoke_hybrid_llm, extract_json_from_text
from decision_engine.input_layer.schemas import ArchitectureNode, UserIdea
from decision_engine.tree.tree_schemas import AgentUncertainty, ProjectState, StateMutation

# Ensure we have our structured output schemas
class PlayerBResponse(BaseModel):
    architecture: ArchitectureNode
    based_on: str

class UncertaintyListResponse(BaseModel):
    uncertainties: List[AgentUncertainty]

def llm_baseline(idea: UserIdea, constraints: List[str]) -> ArchitectureNode:
    prompt = f"""
    Design a software architecture for the following idea:
    WHAT: {idea.what}
    WHY: {idea.why}
    HOW: {idea.how_raw}
    
    Constraints you must satisfy:
    {constraints}
    
    Return a strictly formatted JSON object matching this schema (do NOT include markdown formatting, just raw JSON):
    {{
        "inputs": ["str"],
        "processing": ["str"],
        "decision": ["str"],
        "output": ["str"],
        "capabilities": ["str"],
        "data_required": ["str"],
        "resources_required": ["str"],
        "constraints": ["str"],
        "evidence_provenance": [],
        "architectural_decisions": {{
            "compute_location": "str",
            "inference_strategy": "str",
            "storage_location": "str",
            "connectivity_strategy": "str",
            "input_modality": "str",
            "decision_mechanism": "str",
            "human_approval": "str",
            "deployment_model": "str"
        }}
    }}
    """
    
    response = invoke_hybrid_llm(prompt, temperature=0.3)
    data = extract_json_from_text(response.content)
    
    # Coerce strings to lists for Pydantic validation
    for field in ["inputs", "processing", "decision", "output", "capabilities", "data_required", "resources_required", "constraints", "evidence_provenance"]:
        if field in data and isinstance(data[field], str):
            data[field] = [data[field]]
            
    return ArchitectureNode(**data)

def llm_generate_player_b(
    project_state: ProjectState, 
    kb_evidence: str, 
    previous_arch: Optional[ArchitectureNode] = None, 
    adaptation_reason: Optional[str] = None
) -> PlayerBResponse:
    
    prompt = f"""
    You are an expert AI architect generating a robust architecture grounded in historical evidence.
    
    Project Idea:
    WHAT: {project_state.user_idea.what}
    WHY: {project_state.user_idea.why}
    HOW: {project_state.user_idea.how_raw}
    
    Current Constraints:
    {project_state.current_constraints}
    
    Knowledge Base Evidence (Use this to justify decisions!):
    {kb_evidence}
    """
    
    if previous_arch:
        prompt += f"""
        Previous Architecture:
        {previous_arch.model_dump_json()}
        
        Adaptation Reason (Why you must change it):
        {adaptation_reason}
        
        You must adapt the previous architecture to satisfy the adaptation reason while keeping unaffected parts intact.
        """
        
    prompt += """
    Return a strictly formatted JSON object matching this schema (do NOT include markdown formatting, just raw JSON):
    {
        "architecture": {
            "inputs": ["str"],
            "processing": ["str"],
            "decision": ["str"],
            "output": ["str"],
            "capabilities": ["str"],
            "data_required": ["str"],
            "resources_required": ["str"],
            "constraints": ["str"],
            "evidence_provenance": ["<list of KB IDs or Pattern names used>"],
            "architectural_decisions": {
                "compute_location": "str",
                "inference_strategy": "str",
                "storage_location": "str",
                "connectivity_strategy": "str",
                "input_modality": "str",
                "decision_mechanism": "str",
                "human_approval": "str",
                "deployment_model": "str"
            }
        },
        "based_on": "A short sentence explaining why you made these specific architectural choices."
    }
    """
    
    response = invoke_hybrid_llm(prompt, temperature=0.3)
    data = extract_json_from_text(response.content)
    
    # Simple repair if empty
    if not data:
        raise ValueError(f"Failed to parse JSON from LLM: {response.content}")
        
    arch_data = data.get("architecture", {})
    for field in ["inputs", "processing", "decision", "output", "capabilities", "data_required", "resources_required", "constraints", "evidence_provenance"]:
        if field in arch_data and isinstance(arch_data[field], str):
            arch_data[field] = [arch_data[field]]
            
    return PlayerBResponse(**data)

def llm_find_uncertainties(architecture: ArchitectureNode, project_state: ProjectState) -> List[AgentUncertainty]:
    import uuid
    prompt = f"""
    Analyze the following architecture and the known project constraints.
    Identify facts or resources that the architecture DEPENDS ON, but whose availability is UNKNOWN.
    
    Architecture Data Required: {architecture.data_required}
    Architecture Resources Required: {architecture.resources_required}
    Architecture Capabilities: {architecture.capabilities}
    
    Known Constraints (these are already facts, do NOT ask about these):
    {project_state.current_constraints}
    
    For each uncertainty you identify, you must also hypothesize the two branching paths:
    1. YES branch: What constraint is added, and what is the candidate ArchitectureNode?
    2. NO branch: What constraint is added, and what is the candidate ArchitectureNode?
    
    Return a strictly formatted JSON object containing a list of uncertainties matching this exact schema (do NOT include markdown formatting, just raw JSON):
    {{
        "uncertainties": [
            {{
                "id": "uuid",
                "question_text": "Is [X] available?",
                "question_target": "short_name",
                "unknown_fact": "The specific fact that is unknown",
                "importance": "High/Medium/Low",
                "yes_mutation": {{
                    "add_constraints": ["..."],
                    "remove_constraints": []
                }},
                "no_mutation": {{
                    "add_constraints": ["..."],
                    "remove_constraints": []
                }},
                "yes_candidate_architecture": {{
                    "inputs": ["str"], "processing": ["str"], "decision": ["str"], "output": ["str"],
                    "capabilities": ["str"], "data_required": ["str"], "resources_required": ["str"], "constraints": ["str"], "evidence_provenance": [],
                    "architectural_decisions": {{
                        "compute_location": "str", "inference_strategy": "str", "storage_location": "str", "connectivity_strategy": "str",
                        "input_modality": "str", "decision_mechanism": "str", "human_approval": "str", "deployment_model": "str"
                    }}
                }},
                "no_candidate_architecture": {{
                    "inputs": ["str"], "processing": ["str"], "decision": ["str"], "output": ["str"],
                    "capabilities": ["str"], "data_required": ["str"], "resources_required": ["str"], "constraints": ["str"], "evidence_provenance": [],
                    "architectural_decisions": {{
                        "compute_location": "str", "inference_strategy": "str", "storage_location": "str", "connectivity_strategy": "str",
                        "input_modality": "str", "decision_mechanism": "str", "human_approval": "str", "deployment_model": "str"
                    }}
                }}
            }}
        ]
    }}
    """
    
    response = invoke_hybrid_llm(prompt, temperature=0.3)
    data = extract_json_from_text(response.content)
    
    if not data or "uncertainties" not in data:
        return []
        
    res = []
    for unc in data["uncertainties"]:
        unc["id"] = str(uuid.uuid4())
        
        # Coerce strings to lists in candidate architectures
        for arch_key in ["yes_candidate_architecture", "no_candidate_architecture"]:
            if arch_key in unc:
                arch_data = unc[arch_key]
                for field in ["inputs", "processing", "decision", "output", "capabilities", "data_required", "resources_required", "constraints", "evidence_provenance"]:
                    if field in arch_data and isinstance(arch_data[field], str):
                        arch_data[field] = [arch_data[field]]
                        
        res.append(AgentUncertainty(**unc))
        
    return res
