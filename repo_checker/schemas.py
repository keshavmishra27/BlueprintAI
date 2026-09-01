from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from enum import Enum

class EvidenceType(str, Enum):
    DEPENDENCY_DECLARED = "DEPENDENCY_DECLARED"
    IMPORT_OBSERVED = "IMPORT_OBSERVED"
    CONFIGURED = "CONFIGURED"
    INSTANTIATED = "INSTANTIATED"
    USED = "USED"
    EXPOSED = "EXPOSED"

class Evidence(BaseModel):
    source_file: str
    location: str
    evidence_type: EvidenceType
    observed_entity: str
    confidence: float

class RepositoryArchitectureArtifact(BaseModel):
    components: List[str]
    databases: List[str]
    frameworks: List[str]
    evidence: List[Evidence]
    manifests_found: List[str] = []

class GapCategory(str, Enum):
    MATCH = "MATCH"
    MISSING = "MISSING"
    EXTRA = "EXTRA"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"

class GapFinding(BaseModel):
    category: GapCategory
    expected: str
    observed: Optional[str] = None
    evidence: List[Evidence] = []
    
class GapReport(BaseModel):
    findings: List[GapFinding]
    coverage_score: float
    requirement_set_fingerprint: str = ""
