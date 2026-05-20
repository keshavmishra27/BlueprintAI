from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
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

    # Backward-compatible alias (legacy column name in older DBs)
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


class SwotAnalysis(Base):
    __tablename__ = "swot_analyses"

    id = Column(Integer, primary_key=True, index=True)
    subject_name = Column(String, nullable=False)
    subject_type = Column(String, nullable=False)  # "project" | "idea"
    description = Column(Text, nullable=False)
    result_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
