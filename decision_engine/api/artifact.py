from pydantic import BaseModel
from typing import List, Dict, Any

class ArchitectureDecisionArtifact(BaseModel):
    idea: str
    winning_path_id: str
    components: List[str]
    technologies: List[str]
    databases: List[str]
    interfaces: List[str]
    data_flows: List[str]
    decisions: Dict[str, str]
    constraints: List[str]
    dependencies: List[str]
    pareto_frontier: List[str]
    governance: Dict[str, Any]
    fingerprints: Dict[str, str]
    explanation: str
