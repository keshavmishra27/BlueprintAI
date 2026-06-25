from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import synonym
from .database import Base
class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String, nullable=False)
    domains = Column(JSON, nullable=False, default=list)
    questions_json = Column(JSON, nullable=False, default=list)
    scores = Column(JSON, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    transcript = synonym("questions_json")
class RepoAnalysis(Base):
    __tablename__ = "repo_analyses"
    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String, nullable=False)
    github_url = Column(String, nullable=False)
    result_json = Column(JSON, nullable=False, default=dict)
    static_analysis_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
class IdeaValidation(Base):
    __tablename__ = "idea_validations"
    id = Column(Integer, primary_key=True, index=True)
    idea_text = Column(Text, nullable=False)
    check_result_json = Column(JSON, nullable=True)
    refine_result_json = Column(JSON, nullable=True)
    search_sources_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
class BackgroundTask(Base):
    """Tracks async CrewAI job status so the UI can poll for results."""
    __tablename__ = "background_tasks"
    id = Column(String, primary_key=True)          
    task_type = Column(String, nullable=False)      
    status = Column(String, default="pending")      
    payload_json = Column(JSON, nullable=True)      
    result_json = Column(JSON, nullable=True)       
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
class WebhookRepo(Base):
    """A repo registered to receive automatic CrewAI analysis on every push."""
    __tablename__ = "webhook_repos"
    id = Column(Integer, primary_key=True, index=True)
    github_url = Column(String, nullable=False, unique=True)
    student_name = Column(String, nullable=False)
    secret = Column(String, nullable=True)         
    active = Column(Boolean, default=True)
    last_push_sha = Column(String, nullable=True)
    last_task_id = Column(String, nullable=True)   
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
class SkillGapReport(Base):
    """Nightly curator-agent report: skill gaps + recommended project ideas."""
    __tablename__ = "skill_gap_reports"
    id = Column(Integer, primary_key=True, index=True)
    report_json = Column(JSON, nullable=False, default=dict)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
