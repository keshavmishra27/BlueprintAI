from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from .source import SourceEvidence

class OutcomeEnum(str, Enum):
    winner = "winner"
    runner_up = "runner_up"
    finalist = "finalist"
    unknown = "unknown"

class DecisionFeatures(BaseModel):
    problem_type: List[str] = Field(default_factory=list)
    solution_type: List[str] = Field(default_factory=list)
    primary_value: List[str] = Field(default_factory=list)
    user_type: List[str] = Field(default_factory=list)
    workflow_intervention: bool = Field(default=False)
    requires_ml: bool = Field(default=False)
    requires_llm: bool = Field(default=False)
    prototype_complexity: str = Field(default="unknown") # low, medium, high
    measurable_impact: bool = Field(default=False)

class SIHProject(BaseModel):
    id: str = Field(description="Unique ID, e.g., sih_2024_001")
    hackathon: str = Field(default="Smart India Hackathon")
    edition: str = Field(description="Year of the hackathon")
    problem_domain: List[str] = Field(description="High-level domains like Healthcare, Agriculture, etc.")
    subdomains: List[str] = Field(default_factory=list, description="Specific subdomains")
    problem_statement: str = Field(description="Original problem statement if available")
    
    what: str = Field(description="What was built, explained in plain English")
    why: str = Field(description="What problem required the solution")
    how: str = Field(description="How the proposed solution actually works")
    
    technical_approach: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    key_components: List[str] = Field(default_factory=list)
    
    innovation_or_differentiation: Optional[str] = None
    measurable_or_claimed_impact: Optional[str] = None
    
    outcome: OutcomeEnum = Field(default=OutcomeEnum.unknown)
    outcome_verified: bool = Field(default=False, description="True if evidence explicitly confirms outcome")
    
    decision_features: DecisionFeatures = Field(default_factory=DecisionFeatures)
    
    sources: List[SourceEvidence] = Field(default_factory=list)
