from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field, model_validator
import uuid
from datetime import datetime, timezone

Confidence = Literal["High", "Medium", "Low"]
Severity = Literal["Critical", "High", "Medium", "Low", "Info"]
FindingClassification = Literal["Verified Finding", "Probable Concern", "Recommendation"]
SourceType = Literal["workspace_inspection", "search", "git", "terminal_tool", "semantic_analysis"]
CategoryId = Literal[
    "architecture", 
    "code_quality", 
    "security", 
    "testing_reliability", 
    "maintainability", 
    "documentation_hygiene"
]
CheckStatus = Literal["completed", "failed", "unavailable", "skipped"]

class EvidenceItem(BaseModel):
    id: str
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    symbol: Optional[str] = None
    description: str
    source_type: SourceType

class CheckResult(BaseModel):
    name: str
    status: CheckStatus
    summary: str
    exit_code: Optional[int] = None

class AnalysisLimitation(BaseModel):
    area: str
    reason: str
    impact: str
    severity: Severity

class CategoryAssessment(BaseModel):
    score: int = Field(..., ge=0, le=100)
    confidence: Confidence
    evidence_ids: List[str]
    explanation: str
    highest_priority_improvement: str

class Finding(BaseModel):
    id: str
    title: str
    severity: Severity
    classification: FindingClassification
    category: CategoryId
    explanation: str
    impact: str
    recommendation: str
    evidence_ids: List[str]

class PositiveDecision(BaseModel):
    title: str
    evidence_ids: List[str]
    explanation: str

class RecommendedPriority(BaseModel):
    priority_number: int
    action: str
    reason: str
    related_finding_ids: Optional[List[str]] = None

class RepoJudgeAnalysisPayload(BaseModel):
    decision_id: str
    project_name: str
    repo_path: str
    tech_stack: List[str]
    
    overall_confidence: Confidence
    overall_assessment: str
    
    checks: List[CheckResult]
    limitations: List[AnalysisLimitation]
    evidence: List[EvidenceItem]
    
    categories: Dict[CategoryId, CategoryAssessment]
    findings: List[Finding]
    positive_decisions: List[PositiveDecision]
    priorities: List[RecommendedPriority]

    @model_validator(mode='after')
    def validate_referential_integrity(self):
        evidence_ids = set(e.id for e in self.evidence)
        if len(evidence_ids) != len(self.evidence):
            raise ValueError("Duplicate evidence IDs found.")

        finding_ids = set(f.id for f in self.findings)
        if len(finding_ids) != len(self.findings):
            raise ValueError("Duplicate finding IDs found.")

        # Check evidence references in categories
        for cat_id, cat in self.categories.items():
            for e_id in cat.evidence_ids:
                if e_id not in evidence_ids:
                    raise ValueError(f"Category '{cat_id}' references unknown evidence ID '{e_id}'")

        # Check evidence references in findings
        for f in self.findings:
            for e_id in f.evidence_ids:
                if e_id not in evidence_ids:
                    raise ValueError(f"Finding '{f.id}' references unknown evidence ID '{e_id}'")

        # Check evidence references in positive decisions
        for pd in self.positive_decisions:
            for e_id in pd.evidence_ids:
                if e_id not in evidence_ids:
                    raise ValueError(f"Positive decision '{pd.title}' references unknown evidence ID '{e_id}'")

        # Check finding references in priorities
        for p in self.priorities:
            if p.related_finding_ids:
                for f_id in p.related_finding_ids:
                    if f_id not in finding_ids:
                        raise ValueError(f"Priority '{p.priority_number}' references unknown finding ID '{f_id}'")

        # Ensure all required categories exist
        required_categories = {
            "architecture", "code_quality", "security", 
            "testing_reliability", "maintainability", "documentation_hygiene"
        }
        if set(self.categories.keys()) != required_categories:
            missing = required_categories - set(self.categories.keys())
            raise ValueError(f"Missing required categories: {missing}")

        return self

# ---------------------------------------------------------
# RESULT MODELS
# ---------------------------------------------------------

class AnalysisMetadata(BaseModel):
    analysis_id: str
    decision_id: str
    decision_fingerprint: str
    timestamp: str
    schema_version: str
    project_name: str
    tech_stack: List[str]

class OverallResult(BaseModel):
    score: int = Field(..., ge=0, le=100)
    confidence: Confidence
    assessment: str

class SemanticReport(BaseModel):
    metadata: AnalysisMetadata
    overall: OverallResult
    checks: List[CheckResult]
    limitations: List[AnalysisLimitation]
    evidence: List[EvidenceItem]
    categories: Dict[CategoryId, CategoryAssessment]
    findings: List[Finding]
    positive_decisions: List[PositiveDecision]
    priorities: List[RecommendedPriority]

def calculate_overall_score(categories: Dict[CategoryId, CategoryAssessment]) -> int:
    weights = {
        "architecture": 0.25,
        "code_quality": 0.20,
        "security": 0.20,
        "testing_reliability": 0.15,
        "maintainability": 0.15,
        "documentation_hygiene": 0.05
    }
    score = 0.0
    for cat_id, weight in weights.items():
        score += categories[cat_id].score * weight
    return round(score)

def create_result_from_payload(payload: RepoJudgeAnalysisPayload, decision_fingerprint: str) -> SemanticReport:
    analysis_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    schema_version = "1.0.0"

    overall_score = calculate_overall_score(payload.categories)

    metadata = AnalysisMetadata(
        analysis_id=analysis_id,
        decision_id=payload.decision_id,
        decision_fingerprint=decision_fingerprint,
        timestamp=timestamp,
        schema_version=schema_version,
        project_name=payload.project_name,
        tech_stack=payload.tech_stack
    )

    overall = OverallResult(
        score=overall_score,
        confidence=payload.overall_confidence,
        assessment=payload.overall_assessment
    )

    return SemanticReport(
        metadata=metadata,
        overall=overall,
        checks=payload.checks,
        limitations=payload.limitations,
        evidence=payload.evidence,
        categories=payload.categories,
        findings=payload.findings,
        positive_decisions=payload.positive_decisions,
        priorities=payload.priorities
    )

AssessmentStatus = Literal["success", "failure", "unavailable"]

class StructuralLayer(BaseModel):
    status: AssessmentStatus
    report: Optional[Dict[str, Any]] = None

class SemanticLayer(BaseModel):
    status: AssessmentStatus
    report: Optional[SemanticReport] = None

class RepositoryAssessment(BaseModel):
    metadata: AnalysisMetadata
    structural: StructuralLayer
    semantic: SemanticLayer

