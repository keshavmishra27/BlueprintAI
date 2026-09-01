import json
from typing import Dict, Any
from .base import BaseLLMProvider
from backend.app.services.llm_factory import invoke_hybrid_llm, extract_json_from_text

class HybridLLMProvider(BaseLLMProvider):
    def __init__(self, temperature: float = 0.3):
        self.temperature = temperature
        
    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = f"You are a strict JSON outputting agent. Output valid JSON matching this schema: {json.dumps(schema)}"
        
        messages = [
            ("system", system_prompt),
            ("user", prompt)
        ]
        
        response = invoke_hybrid_llm(messages, temperature=self.temperature)
        data = extract_json_from_text(response.content)
        
        if not data:
            raise ValueError(f"Failed to parse structured JSON from hybrid LLM response: {response.content}")
            
        return data
