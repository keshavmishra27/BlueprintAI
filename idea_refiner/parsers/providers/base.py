import abc
from typing import Dict, Any

class BaseLLMProvider(abc.ABC):
    """
    Abstract base class for LLM providers that can perform structured generation.
    """
    @abc.abstractmethod
    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a JSON response that adheres to the provided schema.
        """
        pass
