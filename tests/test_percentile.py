import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import Base
from backend.app.models import AssessmentSession
from backend.app.services.percentile_service import compute_real_percentile


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _scored_session(db, name, domains, weighted, max_w):
    row = AssessmentSession(
        student_name=name,
        domains=domains,
        questions_json=[],
        scores={"weighted_score": weighted, "max_weighted": max_w},
        status="scored",
    )
    db.add(row)
    db.commit()
    return row


def test_percentile_with_cohort(db):
    _scored_session(db, "a", ["Web Development"], 10, 15)
    _scored_session(db, "b", ["Web Development"], 5, 15)
    _scored_session(db, "c", ["Web Development"], 12, 15)
    info = compute_real_percentile(db, ["Web Development"], 12, 15)
    assert info["percentile_source"] == "database_cohort"
    assert info["cohort_size"] == 3
    assert 0 < info["percentile"] < 100


def test_percentile_small_cohort(db):
    info = compute_real_percentile(db, ["ML"], 8, 15)
    assert info["percentile_source"] == "self_score_estimate"
    assert info["cohort_size"] == 0
