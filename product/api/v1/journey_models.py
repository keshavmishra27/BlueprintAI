from typing import List, Dict, Optional, Literal, Set
from pydantic import BaseModel, Field, model_validator, AnyHttpUrl
from pydantic_core import Url
from datetime import datetime
import uuid

Confidence = Literal["High", "Medium", "Low"]
DimensionStatus = Literal["scored", "not_applicable", "not_validated"]
EvidenceClassification = Literal["verified", "reasoned_assessment", "assumption"]
EvidenceSourceType = Literal["user_input", "web_research", "workspace_inspection", "model_reasoning"]
CompetitorRelevance = Literal["Direct", "Adjacent", "Indirect"]
CompetitorGeographyLevel = Literal["Target Geography", "Global", "Global Active in Target", "Prototype/Research"]
LocalCompetitionLevel = Literal["Strong Local Competition", "Moderate Local Competition", "Limited Local Competition", "Insufficient Evidence"]
LocalizationGapLevel = Literal["Strong", "Possible", "Weak", "Not Demonstrated"]
GeographicOpportunityValue = Literal["Strong", "Moderate", "Weak", "Not Demonstrated", "Not Validated", "Not Applicable"]
MarketEvidenceStatus = Literal["complete", "partial", "unavailable"]
ScoreDimensionId = Literal[
    "problem_value",
    "differentiation",
    "technical_feasibility",
    "user_value",
    "execution_scope",
    "market_evidence",
    "geographic_opportunity",
    "technical_depth"
]
RefinementType = Literal["minor_refinement", "major_refinement", "partial_pivot", "major_pivot"]
GeographicStatus = Literal["applicable", "not_applicable", "not_validated"]

class Evidence(BaseModel):
    id: str
    classification: EvidenceClassification
    source_type: EvidenceSourceType
    title: str
    source: Optional[str] = None
    url: Optional[AnyHttpUrl] = None
    description: str
    timestamp: Optional[str] = None

    @model_validator(mode='after')
    def validate_verified_source(self):
        if self.classification == "verified" and self.source_type == "web_research":
            if not self.source:
                raise ValueError("source must be provided for verified web_research evidence.")
        return self

class Competitor(BaseModel):
    name: str
    geography: str
    level: CompetitorGeographyLevel
    relevance: CompetitorRelevance
    relevant_features: List[str]
    similarity_to_idea: str
    strengths: List[str]
    weaknesses: List[str]
    evidence_ids: List[str]

class ScoreDimension(BaseModel):
    status: DimensionStatus
    score_raw: Optional[int] = Field(None, ge=0, le=100)
    confidence: Confidence
    reasoning: str
    main_deduction_reason: Optional[str] = None
    evidence_ids: List[str]

    @model_validator(mode='after')
    def validate_score(self):
        if self.status == "scored":
            if self.score_raw is None:
                raise ValueError("score_raw is required when status is 'scored'")
        else:
            if self.score_raw is not None:
                raise ValueError("score_raw MUST be absent when status is 'not_applicable' or 'not_validated'")
        return self

class IdeaVersion(BaseModel):
    version_type: Literal["original", "refined"]
    refinement_type: Optional[RefinementType] = None
    
    concise_concept: str
    target_users: str
    problem: str
    solution: str
    differentiation: str
    likely_technical_approach: str
    
    score_dimensions: Dict[ScoreDimensionId, ScoreDimension]
    
    overall_confidence: Confidence
    validation_conclusion: Optional[str] = None

    @model_validator(mode='after')
    def validate_dimensions_and_refinement(self):
        required_dims = {
            "problem_value", "differentiation", "technical_feasibility", "user_value", 
            "execution_scope", "market_evidence", "geographic_opportunity", "technical_depth"
        }
        provided_dims = set(self.score_dimensions.keys())
        if provided_dims != required_dims:
            missing = required_dims - provided_dims
            extra = provided_dims - required_dims
            raise ValueError(f"IdeaVersion must contain exactly the 8 predefined dimensions. Missing: {missing}. Extra: {extra}.")
        
        if self.version_type == "refined":
            if not self.refinement_type:
                raise ValueError("refinement_type is required for 'refined' version")
        else:
            if self.refinement_type is not None:
                raise ValueError("refinement_type must be absent for 'original' version")
                
        return self

class GeographicAnalysis(BaseModel):
    status: GeographicStatus
    target_geography: Optional[str] = None
    local_competition_level: Optional[LocalCompetitionLevel] = None
    localization_gap_level: Optional[LocalizationGapLevel] = None
    overall_opportunity: Optional[GeographicOpportunityValue] = None
    reasoning: Optional[str] = None
    evidence_ids: List[str] = []

    @model_validator(mode='after')
    def validate_geography(self):
        if self.status == "not_applicable":
            if self.target_geography is not None or self.local_competition_level is not None or \
               self.localization_gap_level is not None or self.overall_opportunity is not None:
                raise ValueError("Geographic details must not be provided when status is 'not_applicable'.")
        elif self.status == "applicable":
            if not self.target_geography or not self.overall_opportunity or \
               not self.local_competition_level or not self.localization_gap_level:
                raise ValueError("Geographic details are required when status is 'applicable'.")
        return self

class WeakAssumption(BaseModel):
    id: str
    assumption: str
    why_questionable: str
    impact_if_false: str
    validation_method: str
    evidence_ids: List[str]

class TechnicalFeasibility(BaseModel):
    likely_architecture: str
    required_technologies: List[str]
    external_dependencies: List[str]
    data_requirements: List[str]
    major_technical_risks: List[str]
    privacy_security_considerations: List[str]
    cost_sensitive_components: List[str]
    freeform_reasoning: str

class MVP(BaseModel):
    core_user: str
    core_workflow: str
    must_have_features: List[str]
    explicitly_excluded_features: List[str]
    likely_stack: List[str]
    success_criterion: str

class NextValidationStep(BaseModel):
    action: str
    hypothesis_tested: str
    success_signal: str
    failure_signal: str

class IdeaRefinerAnalysisPayload(BaseModel):
    web_research_available: bool
    market_evidence_status: MarketEvidenceStatus
    
    original_idea: IdeaVersion
    refined_idea: IdeaVersion
    
    evidence: List[Evidence]
    competitors: List[Competitor]
    geographic_analysis: GeographicAnalysis
    weak_assumptions: List[WeakAssumption]
    technical_feasibility: TechnicalFeasibility
    
    mvp: MVP
    next_validation_step: NextValidationStep

    @model_validator(mode='after')
    def validate_referential_integrity(self):
        evidence_ids = [e.id for e in self.evidence]
        unique_evidence_ids = set(evidence_ids)
        if len(unique_evidence_ids) != len(evidence_ids):
            raise ValueError("Duplicate evidence IDs found.")
            
        assumption_ids = [a.id for a in self.weak_assumptions]
        unique_assumption_ids = set(assumption_ids)
        if len(unique_assumption_ids) != len(assumption_ids):
            raise ValueError("Duplicate weak-assumption IDs found.")

        for comp in self.competitors:
            for eid in comp.evidence_ids:
                if eid not in unique_evidence_ids:
                    raise ValueError(f"Competitor references unknown evidence ID: {eid}")
                    
        for eid in self.geographic_analysis.evidence_ids:
            if eid not in unique_evidence_ids:
                raise ValueError(f"GeographicAnalysis references unknown evidence ID: {eid}")
                
        for asm in self.weak_assumptions:
            for eid in asm.evidence_ids:
                if eid not in unique_evidence_ids:
                    raise ValueError(f"WeakAssumption references unknown evidence ID: {eid}")

        for idea in (self.original_idea, self.refined_idea):
            for dim, dim_data in idea.score_dimensions.items():
                for eid in dim_data.evidence_ids:
                    if eid not in unique_evidence_ids:
                        raise ValueError(f"ScoreDimension '{dim}' references unknown evidence ID: {eid}")

        return self

class DimensionComparison(BaseModel):
    dimension: ScoreDimensionId
    original_score: Optional[int] = None
    refined_score: Optional[int] = None
    delta: Optional[int] = None

class IdeaRefinerMetadata(BaseModel):
    analysis_id: str
    timestamp: str
    schema_version: str

class IdeaRefinerScores(BaseModel):
    weighted_original_score: int
    weighted_refined_score: int
    score_improvement: int
    
    original_coverage: int
    refined_coverage: int
    
    original_provisional: bool
    refined_provisional: bool

    dimension_comparisons: List[DimensionComparison]

class IdeaRefinerResult(BaseModel):
    metadata: IdeaRefinerMetadata
    scores: IdeaRefinerScores
    analysis: IdeaRefinerAnalysisPayload

from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.append(str(base_dir))
from decision_engine.tree.tree_schemas import PathNode

class StartJourneyRequest(BaseModel):
    what: str
    why: str
    how: str
    constraints: List[str]
    requirements: List[Dict]
    gemini_baseline_architecture: Dict
    player_b_architecture: Dict
    uncertainties: List[Dict]
    optimization_preferences: Optional[Dict[str, Any]] = None

class AnswerQuestionRequest(BaseModel):
    session_id: str
    selected_option: str
    new_player_b_architecture: Optional[Dict] = None
    new_uncertainties: Optional[List[Dict]] = None

class JourneyStepResponse(BaseModel):
    session_id: str
    is_complete: bool
    current_architecture: Optional[Dict] = None
    current_constraints: Optional[List[str]] = None
    current_requirements: Optional[List[Dict]] = None
    current_battle_result: Optional[Dict] = None
    current_question: Optional[Dict] = None
    decision_impact: Optional[int] = None
    trace_so_far: List[Dict]
    decision_graph: List[Dict] = []
    best_path_id: Optional[str] = None
    final_architecture: Optional[Dict] = None
    decision_id: Optional[str] = None
    decision_fingerprint: Optional[str] = None
