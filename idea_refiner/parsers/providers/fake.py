import json
from typing import Dict, Any
from .base import BaseLLMProvider

class FakeLLMProvider(BaseLLMProvider):
    def __init__(self, predefined_responses: Dict[str, Dict[str, Any]]):
        self.predefined_responses = predefined_responses
        self.call_count = 0

    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        self.call_count += 1
        
        if "extract the explicit and inferred requirements" in prompt:
            return self.predefined_responses.get("requirements", {})
        elif "propose 2 to 3 distinct architectural approaches" in prompt:
            return self.predefined_responses.get("architectures", {})
            
        raise ValueError(f"No fake response configured for prompt: {prompt}")
