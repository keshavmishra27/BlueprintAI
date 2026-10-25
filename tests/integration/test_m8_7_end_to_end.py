import pytest
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from product.db.session import Base
from product.service import ProductService
from product.agent.tools import AgentTools
from product.workspace.binding import write_binding
from benchmark_suite.level6.control_plane.supervisor import BoundedSupervisor, SupervisorState

@pytest.fixture
def test_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def product_service(test_db_session, monkeypatch):
    class MockArtifact:
        components = ["FastAPI", "PostgreSQL"]
        decisions = {"db": "PostgreSQL"}
        scores = {"performance": 0.9}
        governance = {"action": "RECOMMEND", "severity": "INFO"}
        winner_id = "mock-winner"
        candidates_evaluated = []
        pareto_frontier_ids = []
        explanation = "mock explanation"
        
    class MockOrchestrator:
        def __init__(self, *args, **kwargs): pass
        def refine(self, *args, **kwargs): return MockArtifact()
        
    import product.service
    monkeypatch.setattr(product.service, "Orchestrator", MockOrchestrator)
    return ProductService(test_db_session)

def test_m8_7_happy_path(tmp_path: Path, product_service: ProductService):
    class DummyContext:
        def model_dump(self):
            return {"mocked": "context"}
            
    decision = product_service.analyze_idea(
        "A simple FastAPI application", 
        context=DummyContext()
    )
    
    write_binding(
        workspace_dir=tmp_path,
        root_decision_id=decision.id,
        decision_id=decision.id,
        decision_fingerprint=decision.decision_fingerprint,
        requirement_set_fingerprint=decision.requirement_set_fingerprint
    )
    
    tools = AgentTools(workspace_dir=tmp_path, service=product_service)
    
    def mock_verify_callback(decision_id, workspace_dir):
        if not hasattr(mock_verify_callback, 'call_count'):
            mock_verify_callback.call_count = 0
            
        mock_verify_callback.call_count += 1
        
        class MockGapReport:
            pass
        
        report = MockGapReport()
        if mock_verify_callback.call_count == 1:
            report.findings = [{"category": "MISSING", "expected": "FastAPI"}]
        else:
            report.findings = []
            
        return report

    supervisor = BoundedSupervisor(
        run_id="run-1",
        scenario_id="scenario-1",
        decision_id=decision.id,
        workspace_dir=tmp_path,
        max_retries=3,
        verify_callback=mock_verify_callback
    )
    
    def mock_issue_prompt(instruction_type, prompt_text, target_artifacts):
        from benchmark_suite.level6.control_plane.handshake import ResponsePacket, ExecutionStatus
        import uuid
        
        if instruction_type.value == "IMPLEMENT":
            pass
        elif instruction_type.value == "FIX_GAPS":
            pass
            
        return ResponsePacket(
            run_id="run-1",
            scenario_id="scenario-1",
            step_id=1,
            invocation_id=str(uuid.uuid4()),
            prompt_id="mock-prompt-id",
            status=ExecutionStatus.SUCCESS
        )
        
    supervisor._issue_prompt = mock_issue_prompt
    
    final_state = supervisor.run_loop()
    
    assert final_state == SupervisorState.DONE
    assert mock_verify_callback.call_count == 2
    
    active = tools.get_active_contract()
    assert active.id == decision.id

def test_m8_7_adversarial_binding(tmp_path: Path, product_service: ProductService):
    class DummyContext:
        def model_dump(self):
            return {"mocked": "context"}
            
    decision_x = product_service.analyze_idea("Decision X Idea", context=DummyContext())
    decision_y = product_service.analyze_idea("Decision Y Idea", context=DummyContext())
    
    write_binding(
        workspace_dir=tmp_path,
        root_decision_id=decision_x.id,
        decision_id=decision_x.id,
        decision_fingerprint=decision_x.decision_fingerprint,
        requirement_set_fingerprint=decision_x.requirement_set_fingerprint
    )
    
    tools = AgentTools(workspace_dir=tmp_path, service=product_service)
    
    assert tools.get_contract(decision_x.id).id == decision_x.id
    
    with pytest.raises(ValueError, match="REJECTED"):
        tools.get_contract(decision_y.id)
        
    with pytest.raises(ValueError, match="REJECTED"):
        tools.verify_repository(decision_y.id)
