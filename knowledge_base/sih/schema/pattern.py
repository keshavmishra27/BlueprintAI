from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class ConfidenceEnum(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class SIHPattern(BaseModel):
    pattern_id: str = Field(description="Unique ID for the pattern")
    domain: str = Field(description="Domain this pattern applies to")
    pattern: str = Field(description="The semantic pattern discovered")
    observed_in_projects: List[str] = Field(description="List of project IDs where this pattern was observed")
    evidence: List[str] = Field(description="Evidence strings (e.g. 'sih_2023_001: workflow optimization...')")
    confidence: ConfidenceEnum = Field(default=ConfidenceEnum.medium)
