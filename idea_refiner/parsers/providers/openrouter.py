from typing import Dict, Any
from .base import BaseLLMProvider

class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, model: str = "openai/gpt-4o", api_key: str = None):
        pass

    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("OpenRouter provider is a stub")
