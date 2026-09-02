from pydantic import BaseModel
from typing import Optional

class EpistemicResolution(BaseModel):
    """
    A PROPOSED epistemic state transition derived from a human answer.
    This is intentionally NOT authorized to mutate the graph directly. 
    The Decision Engine must validate this against its ontology and state.
    """
    target: str                  # e.g., 'student_hardware'
    normalized_value: str        # e.g., 'low_end'
    provenance: str              # e.g., 'HUMAN_EXPLICIT'
    source_answer: str           # e.g., 'Most students have low-end phones.'

class EpistemicResolver:
    """
    Domain-layer parser responsible for interpreting natural language answers 
    and proposing a mapping to existing ontology targets.
    """
    def __init__(self, provider):
        """
        :param provider: The LLM Provider (BaseLLMProvider) to use for interpretation.
        """
        self.provider = provider
        
    def resolve(self, target: str, question: str, human_answer: str) -> EpistemicResolution:
        """
        Takes a human answer and proposes an epistemic resolution.
        """
        prompt = (
            f"Question asked: {question}\n"
            f"Epistemic target: {target}\n"
            f"Human answer: {human_answer}\n"
            "Map the human's answer to a normalized value for this target."
        )
        
        schema = {
            "type": "object",
            "properties": {
                "normalized_value": {"type": "string"}
            },
            "required": ["normalized_value"]
        }
        
        # In a real scenario, the LLM provider parses the answer.
        # For M13-C0 with FakeLLMProvider, it returns a mocked dictionary.
        response = self.provider.generate_structured(prompt, schema)
        
        return EpistemicResolution(
            target=target,
            normalized_value=response.get("normalized_value", "unknown"),
            provenance="HUMAN_EXPLICIT",
            source_answer=human_answer
        )
