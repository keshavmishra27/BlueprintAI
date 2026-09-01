from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict

class ProvenanceType(str, Enum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"
    UNKNOWN = "unknown"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TimeUnit(str, Enum):
    MILLISECONDS = "milliseconds"
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"

class QualitativeHorizon(str, Enum):
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    SEVERAL = "several"
    LONG_TERM = "long_term"

class ConnectivityType(str, Enum):
    CONTINUOUS = "continuous"
    INTERMITTENT = "intermittent"
    OFFLINE = "offline"

class DeploymentTarget(str, Enum):
    CLOUD = "cloud"
    EDGE = "edge"
    ON_DEVICE = "on_device"
    ON_PREMISE = "on_premise"

class HardwareProfile(str, Enum):
    HIGH_END_SERVER = "high_end_server"
    LOW_END_SERVER = "low_end_server"
    CONSUMER_MOBILE = "consumer_mobile"
    LOW_POWER_IOT = "low_power_iot"

class Provenance(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    type: ProvenanceType
    source_quote: Optional[str] = Field(
        default=None, 
        description="Exact quote from user input if EXPLICIT"
    )
    confidence: Optional[ConfidenceLevel] = None
    
    inference_basis_requirement_ids: List[str] = Field(
        default_factory=list,
        description="IDs of other requirements that logically imply this one, if INFERRED."
    )

    @model_validator(mode='after')
    def check_provenance_consistency(self) -> 'Provenance':
        if self.type == ProvenanceType.EXPLICIT and not self.source_quote:
            raise ValueError("EXPLICIT provenance must include a source_quote.")
        
        if self.type == ProvenanceType.INFERRED and not self.inference_basis_requirement_ids:
            raise ValueError("INFERRED provenance must include inference_basis_requirement_ids.")
            
        return self

class BaseRequirement(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    id: str = Field(..., description="Unique identifier for traceability, e.g., 'R-01'")
    provenance: Provenance
    
    @model_validator(mode='after')
    def check_unknown_provenance(self) -> 'BaseRequirement':
        payload_fields = [k for k in self.model_fields.keys() if k not in ('id', 'provenance')]
        
        has_values = False
        for field in payload_fields:
            if getattr(self, field) is not None:
                has_values = True
                break
                
        if not has_values and self.provenance.type != ProvenanceType.UNKNOWN:
            raise ValueError(f"Provenance must be UNKNOWN if all values are None for {self.__class__.__name__}")
        
        if has_values and self.provenance.type == ProvenanceType.UNKNOWN:
            raise ValueError(f"Provenance cannot be UNKNOWN if a value is provided for {self.__class__.__name__}")
            
        return self

class PredictionHorizon(BaseRequirement):
    exact_value: Optional[float] = None
    unit: Optional[TimeUnit] = None
    qualitative: Optional[QualitativeHorizon] = None

    @model_validator(mode='after')
    def check_horizon_conflicts(self) -> 'PredictionHorizon':
        if self.exact_value is not None and self.qualitative is not None:
            raise ValueError("PredictionHorizon cannot have both exact_value and qualitative set.")
        return self

class LatencyRequirement(BaseRequirement):
    max_latency_ms: Optional[int] = Field(
        default=None,
        description="Strict measurable latency constraint, completely decoupled from prediction horizon."
    )

    @model_validator(mode='after')
    def check_latency_value(self) -> 'LatencyRequirement':
        if self.max_latency_ms is not None and self.max_latency_ms <= 0:
            raise ValueError("max_latency_ms must be strictly greater than 0.")
        return self

class DataFreshnessRequirement(BaseRequirement):
    real_time_streams_required: Optional[bool] = None
    historical_data_required: Optional[bool] = None

class NetworkRequirement(BaseRequirement):
    connectivity: Optional[ConnectivityType] = None

class DeploymentRequirement(BaseRequirement):
    target: Optional[DeploymentTarget] = None
    hardware_profile: Optional[HardwareProfile] = None

class RequirementArtifact(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    """
    The authoritative set of facts extracted from the user's idea.
    No architectural decisions are allowed here. 
    If a requirement is not specified or logically derivable, its provenance should be marked UNKNOWN.
    """
    prediction_horizon: PredictionHorizon
    latency: LatencyRequirement
    data_freshness: DataFreshnessRequirement
    network: NetworkRequirement
    deployment: DeploymentRequirement

    @model_validator(mode='after')
    def check_artifact_consistency(self) -> 'RequirementArtifact':
        reqs = [
            self.prediction_horizon,
            self.latency,
            self.data_freshness,
            self.network,
            self.deployment
        ]
        
        seen_ids = set()
        for r in reqs:
            if r.id in seen_ids:
                raise ValueError(f"Duplicate requirement ID found: {r.id}")
            seen_ids.add(r.id)
            
        for r in reqs:
            if r.provenance.type == ProvenanceType.INFERRED:
                for basis_id in r.provenance.inference_basis_requirement_ids:
                    if basis_id not in seen_ids:
                        raise ValueError(f"Requirement {r.id} infers from nonexistent ID {basis_id}")
                        
        return self
