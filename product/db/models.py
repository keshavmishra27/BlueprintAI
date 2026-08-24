import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .session import Base

def generate_uuid():
    return str(uuid.uuid4())

class DecisionRecord(Base):
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, default=generate_uuid)
    idea_text = Column(String, nullable=False)
    parent_id = Column(String, ForeignKey("decisions.id"), nullable=True)
    
    # Store the core data as JSON blobs
    architecture_json = Column(JSON, nullable=False)
    governance_json = Column(JSON, nullable=False)
    alternatives_json = Column(JSON, nullable=True)
    
    # Fingerprints for identity tracking
    decision_fingerprint = Column(String, nullable=False)
    graph_fingerprint = Column(String, nullable=False)
    context_fingerprint = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("DecisionRecord", remote_side=[id], backref="children")
    gap_reports = relationship("GapReportRecord", back_populates="decision")
    
    # Note: For refinements, source_decision_id and target_decision_id link to DecisionRecord

class GapReportRecord(Base):
    __tablename__ = "gap_reports"

    id = Column(String, primary_key=True, default=generate_uuid)
    decision_id = Column(String, ForeignKey("decisions.id"), nullable=False)
    
    repository_fingerprint = Column(String, nullable=False)
    
    # Details of the gap
    expected_architecture_json = Column(JSON, nullable=False)
    actual_architecture_json = Column(JSON, nullable=False)
    findings_json = Column(JSON, nullable=False)
    evidence_json = Column(JSON, nullable=False)
    alignment_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    decision = relationship("DecisionRecord", back_populates="gap_reports")
    refinements = relationship("RefinementRecord", back_populates="gap_report")

class RefinementRecord(Base):
    __tablename__ = "refinements"

    id = Column(String, primary_key=True, default=generate_uuid)
    source_decision_id = Column(String, ForeignKey("decisions.id"), nullable=False)
    target_decision_id = Column(String, ForeignKey("decisions.id"), nullable=False)
    gap_report_id = Column(String, ForeignKey("gap_reports.id"), nullable=True)
    
    problem_detected = Column(String, nullable=False)
    preserved_json = Column(JSON, nullable=False)
    applied_exploration = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source_decision = relationship("DecisionRecord", foreign_keys=[source_decision_id])
    target_decision = relationship("DecisionRecord", foreign_keys=[target_decision_id])
    gap_report = relationship("GapReportRecord", back_populates="refinements")
