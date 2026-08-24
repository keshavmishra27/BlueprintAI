import hashlib
from typing import List, Dict, Any
from .base import BaseIdeaParser
from .providers.base import BaseLLMProvider
from decision_engine.input_layer.schemas import UnvalidatedArchitectureHypothesis

class LLMIdeaParser(BaseIdeaParser):
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        
    def _get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "hypotheses": {
                    "type": "array",
                    "description": "Provide 2 to 3 distinct architectural candidate approaches to solve the problem.",
                    "items": {
                        "type": "object",
                        "properties": {
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
                        "required": ["inputs", "processing", "decision", "output", "capabilities", "semantic_dependencies", "data_required", "resources_required", "constraints", "architectural_decisions"]
                    }
                }
            },
            "required": ["hypotheses"]
        }
        
    def parse_idea_to_graph(self, idea: str) -> List[UnvalidatedArchitectureHypothesis]:
        prompt = f"Analyze the following idea and propose 2 to 3 distinct architectural approaches to implement it. Do NOT assign any feasibility, confidence, or status. Idea: {idea}"
        
        response = self.provider.generate_structured(prompt, self._get_schema())
        
        hypotheses = []
        for item in response.get("hypotheses", []):
            # Enforce boundary: strictly strip authority fields
            for forbidden_key in ["status", "feasibility", "confidence", "candidate_status"]:
                item.pop(forbidden_key, None)
                
            hypothesis = UnvalidatedArchitectureHypothesis(
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
                    "parser": "LLMIdeaParser",
                    "model": getattr(self.provider, "model", "unknown"),
                    "source_idea_hash": hashlib.sha256(idea.encode()).hexdigest()
                }
            )
            hypotheses.append(hypothesis)
            
        return hypotheses
