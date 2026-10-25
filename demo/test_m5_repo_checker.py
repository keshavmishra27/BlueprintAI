import sys
from pathlib import Path
import os
import tempfile

base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from decision_engine.api.artifact import ArchitectureDecisionArtifact
from repo_checker.schemas import RepositoryArchitectureArtifact, Evidence, GapCategory
from repo_checker.gap_engine import GapEngine
from repo_checker.extractor import RepoExtractor

def test_m5_repo_checker():
    print("\n==================================================")
    print("      M5: REPO CHECKER INTEGRATION TESTS          ")
    print("==================================================")
    
    expected_artifact = ArchitectureDecisionArtifact(
        idea="A backend service",
        winning_path_id="seed_1",
        components=["FastAPI", "PostgreSQL", "Redis", "Kafka"],
        technologies=["FastAPI", "PostgreSQL", "Redis", "Kafka"],
        databases=["PostgreSQL", "Redis"],
        interfaces=["REST API"],
        data_flows=[],
        decisions={},
        constraints=[],
        dependencies=[],
        pareto_frontier=["seed_1"],
        governance={},
        fingerprints={},
        explanation=""
    )
    assert expected_artifact.components == ["FastAPI", "PostgreSQL", "Redis", "Kafka"]
    print("[PASS] 1. Contract Fulfillment (Decoupled Artifact)")
    
    actual_artifact = RepositoryArchitectureArtifact(
        components=["FastAPI", "MongoDB", "Elasticsearch", "Nginx"],
        databases=["MongoDB", "Elasticsearch"],
        frameworks=["FastAPI", "Nginx"],
        evidence=[
            Evidence(source_file="req.txt", location="L1", evidence_type="dep", observed_entity="FastAPI", confidence=1.0),
            Evidence(source_file="req.txt", location="L2", evidence_type="dep", observed_entity="MongoDB", confidence=1.0),
            Evidence(source_file="req.txt", location="L3", evidence_type="dep", observed_entity="Elasticsearch", confidence=1.0)
        ]
    )
    
    engine = GapEngine()
    report = engine.evaluate(expected_artifact, actual_artifact)
    
    match_found = False
    mismatch_found = False
    missing_found = False
    extra_found = False
    
    for f in report.findings:
        if f.expected == "FastAPI" and f.category == GapCategory.MATCH:
            match_found = True
        if f.expected == "PostgreSQL" and f.category == GapCategory.MISMATCH and f.observed in ["MongoDB", "Elasticsearch"]:
            mismatch_found = True
        if f.expected == "Kafka" and f.category == GapCategory.MISSING:
            missing_found = True
        if f.category == GapCategory.EXTRA and f.observed == "Nginx":
            extra_found = True
            
    assert match_found, "MATCH failed"
    assert mismatch_found, "MISMATCH failed"
    assert missing_found, "MISSING failed"
    assert extra_found, "EXTRA failed"
    
    print("[PASS] 2. Gap Analysis Matrix (MATCH, MISMATCH, MISSING, EXTRA)")
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        with open(os.path.join(tmpdirname, "requirements.txt"), "w") as f:
            f.write("fastapi\npsycopg2\n")
            
        extractor = RepoExtractor(tmpdirname)
        repo_art = extractor.extract_deterministic()
        rep1 = engine.evaluate(expected_artifact, repo_art)
        
        p_match = any(f.expected == "PostgreSQL" and f.category == GapCategory.MATCH for f in rep1.findings)
        assert p_match, "Failed initial evidence integrity"
        
        with open(os.path.join(tmpdirname, "requirements.txt"), "w") as f:
            f.write("fastapi\npymongo\n")
            
        repo_art_mut = extractor.extract_deterministic()
        rep2 = engine.evaluate(expected_artifact, repo_art_mut)
        
        p_mismatch = any(f.expected == "PostgreSQL" and f.category == GapCategory.MISMATCH and f.observed == "MongoDB" for f in rep2.findings)
        assert p_mismatch, "Evidence mutation did not affect Gap Engine deterministically!"
        
    print("[PASS] 3. Evidence Integrity (Mutating repo evidence changes Gap Engine output)")
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        extractor = RepoExtractor(tmpdirname)
        repo_art_empty = extractor.extract_deterministic()
        rep3 = engine.evaluate(expected_artifact, repo_art_empty)
        
        u_redis = any(f.expected == "Redis" and f.category == GapCategory.UNKNOWN for f in rep3.findings)
        assert u_redis, "Missing evidence resulted in MISSING instead of UNKNOWN"
        
    print("[PASS] 4. Unknown != Missing (Epistemic discipline)")
    print("\nALL 4 M5 ACCEPTANCE TESTS PASSED.")

if __name__ == "__main__":
    test_m5_repo_checker()
