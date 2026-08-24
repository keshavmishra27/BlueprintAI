from typing import Dict, Any
from .base import BaseLLMProvider

class LocalProvider(BaseLLMProvider):
    def __init__(self, model: str = "llama3"):
        pass

    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Local provider is a stub")
