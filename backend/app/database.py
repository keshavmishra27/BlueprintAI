import logging
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
load_dotenv(override=True)
logger = logging.getLogger(__name__)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./group_maker.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def ensure_schema():
    """Create tables and apply lightweight SQLite/Postgres patches."""
    from backend.app import models  
    models.Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    if "assessment_sessions" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("assessment_sessions")}
        if "transcript" in cols and "questions_json" not in cols:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE assessment_sessions "
                        "RENAME COLUMN transcript TO questions_json"
                    )
                )
            logger.info("Migrated assessment_sessions.transcript -> questions_json")
