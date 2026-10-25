import hashlib
from pydantic import BaseModel
from typing import List, Optional
import json
from decision_engine.input_layer.schemas import SemanticClaim

class ExportedCapability(BaseModel):
    capability_id: str
    name: str
    required: bool
    functional_properties: List[SemanticClaim]
    constraints: List[SemanticClaim]
    reference_implementation: str

class CanonicalReferenceArtifact(BaseModel):
    decision_id: str
    winning_path_id: str
    generated_from: str
    decision_rationale: str
    capabilities: List[ExportedCapability]

class ArtifactExporter:
    @staticmethod
    def export(decision_id: str, winning_node, rationale: str) -> CanonicalReferenceArtifact:
        arch = winning_node.architecture
        
        exported_caps = []
        for cap_node in arch.capabilities:
            cap = ExportedCapability(
                capability_id=cap_node.capability_id,
                name=cap_node.name,
                required=True,
                functional_properties=cap_node.functional_properties,
                constraints=cap_node.constraints,
                reference_implementation=cap_node.reference_implementation
            )
            exported_caps.append(cap)
            
        return CanonicalReferenceArtifact(
            decision_id=decision_id,
            winning_path_id=winning_node.id,
            generated_from="BlueprintAI Decision Engine Optimizer (v1)",
            decision_rationale=rationale,
            capabilities=exported_caps
        )
