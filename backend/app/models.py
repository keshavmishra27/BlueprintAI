from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, timezone
class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    id            = Column(Integer, primary_key=True, index=True)
    student_name  = Column(String, nullable=False)
    domains       = Column(JSON, nullable=False, default=list)
    transcript    = Column(JSON, nullable=False, default=list)
    scores        = Column(JSON, nullable=True)
    status        = Column(String, default="active")
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at  = Column(DateTime, nullable=True)