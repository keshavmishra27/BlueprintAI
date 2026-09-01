from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import hashlib

def canonicalize_json(data: Any) -> str:
    """Deterministically stringifies JSON-serializable data."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'))

class DecisionContext(BaseModel):
    ontology_version: str
    registry_policy_hashes: List[str]
    environment_constraints: List[str]
    optimizer_preferences: Dict[str, Any]
    future_scenarios: Optional[List[Dict[str, Any]]] = None
    
    def get_fingerprint(self) -> str:
        data = {
            "ontology_version": self.ontology_version,
            "registry_policy_hashes": sorted(self.registry_policy_hashes),
            "environment_constraints": sorted(self.environment_constraints),
            "optimizer_preferences": self.optimizer_preferences,
            "future_scenarios": sorted(self.future_scenarios, key=lambda s: s["id"]) if self.future_scenarios else None
        }
        canonical_str = canonicalize_json(data)
        return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
