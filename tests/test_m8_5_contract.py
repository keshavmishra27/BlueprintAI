import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from product.db.session import Base
from product.db.models import DecisionRecord
from product.service import ProductService

@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def service(db_session):
    return ProductService(db_session)

def test_a_deterministic_subset_mapping(service):
    decision = service.analyze_idea('Test idea', context=None)
    record = service.repository.get_decision(decision.id)
    
    engine_artifact = service._map_to_engine_artifact(record)
    
    assert engine_artifact.idea == 'Test idea'
    assert engine_artifact.winner_id == decision.id
    assert 'Default Component' in engine_artifact.components or len(engine_artifact.components) > 0
    assert 'canonical' in engine_artifact.fingerprints
    assert engine_artifact.fingerprints['canonical'] == decision.decision_fingerprint
    
def test_b_fingerprint_completeness(service):
    arch = {'components': [{'name': 'A'}], 'decisions': []}
    gov1 = {'action': 'RECOMMEND'}
    gov2 = {'action': 'BLOCK'}
    
    fp1 = service._canonicalize_and_hash(arch, gov1, [])
    fp2 = service._canonicalize_and_hash(arch, gov2, [])
    assert fp1 != fp2, 'Governance change should change fingerprint'
    
    arch2 = {'components': [{'name': 'B'}], 'decisions': []}
    fp3 = service._canonicalize_and_hash(arch2, gov1, [])
    assert fp1 != fp3, 'Architecture change should change fingerprint'

def test_c_canonicalization(service):
    arch1 = {'components': [{'name': 'A'}, {'name': 'B'}], 'decisions': []}
    arch2 = {'components': [{'name': 'B'}, {'name': 'A'}], 'decisions': []}
    
    fp1 = service._canonicalize_and_hash(arch1, {}, [])
    fp2 = service._canonicalize_and_hash(arch2, {}, [])
    
    assert fp1 == fp2, 'Fingerprint should be order-independent for components'

def test_d_immutability(service, db_session):
    decision = service.analyze_idea('Immutability test')
    record = service.repository.get_decision(decision.id)
    
    record.architecture_json = {'components': [{'name': 'Hacked'}]}
    
    with pytest.raises(ValueError, match='is immutable'):
        db_session.commit()
        
    db_session.rollback()

def test_e_and_f_evaluation_fidelity_and_provenance(service, monkeypatch):
    decision = service.analyze_idea('Fidelity test')
    
    record = service.repository.get_decision(decision.id)
    
    class MockRepoArtifact:
        components = ['Sentinel']
        databases = []
        frameworks = []
        evidence = []
        manifests_found = []
    class MockRepoExtractor:
        def __init__(self, *args, **kwargs): pass
        def extract_deterministic(self): return MockRepoArtifact()
        
    import product.service
    monkeypatch.setattr(product.service, 'RepoExtractor', MockRepoExtractor)
    
    gap_report = service.analyze_repository(decision.id, '/dummy')
    assert gap_report is not None
    
    assert gap_report.decision_fingerprint == record.decision_fingerprint
    assert gap_report.requirement_set_fingerprint != gap_report.decision_fingerprint
    
    assert len(gap_report.findings) > 0

def test_g_contract_substitution_rejection(service, monkeypatch):
    decision_x = service.analyze_idea('Decision X')
    
    class MockArtifact:
        components = ['DistinctiveComponentY']
        decisions = {}
        governance = {}
        winner_id = "mock-winner"
        candidates_evaluated = []
        pareto_frontier_ids = []
        explanation = "mock explanation"
    
    class MockOrchestrator:
        def __init__(self, *args, **kwargs): pass
        def refine(self, *args, **kwargs): return MockArtifact()
        
    import product.service
    monkeypatch.setattr(product.service, 'Orchestrator', MockOrchestrator)
    
    decision_y = service.analyze_idea('Decision Y')
    decision_y_refined = service.apply_refinement(decision_y.id, None, 'Swap', [], 'Problem')
    
    record_y_ref = service.repository.get_decision(decision_y_refined.id)
    artifact_y = service._map_to_engine_artifact(record_y_ref)
    
    class MockRepoArtifact:
        components = ['Dummy']
        databases = []
        frameworks = []
        evidence = []
        manifests_found = []
    class MockRepoExtractor:
        def __init__(self, *args, **kwargs): pass
        def extract_deterministic(self): return MockRepoArtifact()
    import product.service
    monkeypatch.setattr(product.service, 'RepoExtractor', MockRepoExtractor)
    
    with pytest.raises(ValueError, match='Provenance violation'):
        service.analyze_repository(decision_x.id, '/dummy', _injected_artifact=artifact_y)
