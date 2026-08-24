import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from product.db.session import Base, get_db
from product.api.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_blueprint.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create the database
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop the database after each test for clean slate
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    # Mock Orchestrator to avoid LLM calls and initialization errors
    class MockArtifact:
        components = ["FastAPI", "PostgreSQL"]
        decisions = {"db": "PostgreSQL"}
        scores = {"performance": 0.9}
        governance = {"action": "RECOMMEND", "severity": "INFO"}
        
    class MockOrchestrator:
        def __init__(self, *args, **kwargs): pass
        def refine(self, *args, **kwargs): return MockArtifact()
        
    import product.service
    monkeypatch.setattr(product.service, "Orchestrator", MockOrchestrator)

    yield TestClient(app)
    app.dependency_overrides.clear()
