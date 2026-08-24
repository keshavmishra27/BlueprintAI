import hashlib
from typing import List, Dict, Any
from idea_refiner.parsers.providers.base import BaseLLMProvider
from decision_engine.input_layer.schemas import UnvalidatedArchitectureHypothesis
from decision_engine.tree.graph import DecisionGraph, GraphState

class GraphGenerator:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        
    def _get_expansion_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "variations": {
                    "type": "array",
                    "description": "Provide 2 to 3 architectural variations for the given seed approach.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "generation_reason": {"type": "string"},
                            "inputs": {"type": "array", "items": {"type": "string"}},
                            "processing": {"type": "array", "items": {"type": "string"}},
                            "decision": {"type": "array", "items": {"type": "string"}},
                            "output": {"type": "array", "items": {"type": "string"}},
                            "capabilities": {"type": "array", "items": {"type": "string"}},
                            "semantic_dependencies": {"type": "array", "items": {"type": "string"}},
                            "data_required": {"type": "array", "items": {"type": "string"}},
                            "resources_required": {"type": "array", "items": {"type": "string"}},
                            "constraints": {"type": "array", "items": {"type": "string"}},
                            "architectural_decisions": {
                                "type": "object",
                                "additionalProperties": {"type": "string"}
                            }
                        },
                        "required": ["generation_reason", "inputs", "processing", "decision", "output", "capabilities", "semantic_dependencies", "data_required", "resources_required", "constraints", "architectural_decisions"]
                    }
                }
            },
            "required": ["variations"]
        }
        
    def expand_seeds(self, seeds: List[UnvalidatedArchitectureHypothesis]) -> List[UnvalidatedArchitectureHypothesis]:
        expanded_hypotheses = []
        seen_signatures = set()
        
        # Add seeds first
        for i, seed in enumerate(seeds):
            seed.id = f"seed_{i}"
            sig = seed.get_signature()
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                expanded_hypotheses.append(seed)
                
        # Ask LLM for variations
        for seed in seeds:
            prompt = f"""
            Analyze the following architectural seed approach. 
            Propose 2-3 specific architectural transformations (e.g., streaming vs batch, NoSQL vs SQL, edge vs cloud).
            Seed details:
            Processing: {seed.processing}
            Constraints: {seed.constraints}
            Capabilities: {seed.capabilities}
            
            Return the variations matching the JSON schema. Do NOT include feasibility or status fields.
            """
            
            response = self.provider.generate_structured(prompt, self._get_expansion_schema())
            
            for j, item in enumerate(response.get("variations", [])):
                # Strip authority fields to prevent injection
                for forbidden_key in ["status", "feasibility", "confidence", "candidate_status"]:
                    item.pop(forbidden_key, None)
                    
                reason = item.pop("generation_reason", "LLM proposed variation")
                
                variation = UnvalidatedArchitectureHypothesis(
                    id=f"{seed.id}_var_{j}",
                    parent_id=seed.id,
                    generation_reason=reason,
                    inputs=item.get("inputs", []),
                    processing=item.get("processing", []),
                    decision=item.get("decision", []),
                    output=item.get("output", []),
                    capabilities=item.get("capabilities", []),
                    semantic_dependencies=item.get("semantic_dependencies", []),
                    data_required=item.get("data_required", []),
                    resources_required=item.get("resources_required", []),
                    constraints=item.get("constraints", []),
                    architectural_decisions=item.get("architectural_decisions", {}),
                    source="llm_generated",
                    hypothesis=True,
                    provenance={
                        "generator": "GraphGenerator",
                        "model": getattr(self.provider, "model", "unknown")
                    }
                )
                
                # Duplicate suppression
                var_sig = variation.get_signature()
                if var_sig not in seen_signatures:
                    seen_signatures.add(var_sig)
                    expanded_hypotheses.append(variation)
                    
        return expanded_hypotheses
