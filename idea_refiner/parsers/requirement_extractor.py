import json
from typing import Dict, Any
from .providers.base import BaseLLMProvider
from ..schema import RequirementArtifact

class RequirementExtractor:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        
    def _get_schema(self) -> Dict[str, Any]:
        return RequirementArtifact.model_json_schema()
        
    def extract_requirements(self, idea: str) -> RequirementArtifact:
        prompt = (
            f"Analyze the following user idea and extract the explicit and inferred requirements. "
            f"Do NOT invent precision where it is not stated (e.g., if 'several hours' is mentioned, "
            f"use QualitativeHorizon 'several', do not invent an exact_value). "
            f"If a requirement is not mentioned and cannot be logically inferred, mark its provenance as UNKNOWN "
            f"and set its value fields to null/None. "
            f"Ensure every requirement has a unique 'id' (e.g., R-01).\n\n"
            f"Idea: {idea}"
        )
        
        response = self.provider.generate_structured(prompt, self._get_schema())
        
        return RequirementArtifact.model_validate(response)
