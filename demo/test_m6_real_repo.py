import sys
import os
import tempfile
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from decision_engine.api.artifact import ArchitectureDecisionArtifact
from repo_checker.schemas import GapCategory, GapReport
from repo_checker.gap_engine import GapEngine
from repo_checker.extractor import RepoExtractor

def evaluate_repo(repo_path: str) -> GapReport:
    expected_artifact = ArchitectureDecisionArtifact(
        idea="A backend service",
        winning_path_id="seed_1",
        components=["FastAPI"],
        technologies=["FastAPI"],
        databases=[],
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
    
    extractor = RepoExtractor(repo_path)
    repo_artifact = extractor.extract_deterministic()
    
    engine = GapEngine()
    return engine.evaluate(expected_artifact, repo_artifact)

def test_m6_mutations():
    print("\n==================================================")
    print("      M6: REAL REPOSITORY MUTATION WORKFLOW       ")
    print("==================================================")
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        req_path = os.path.join(tmpdirname, "requirements.txt")
        app_path = os.path.join(tmpdirname, "app.py")
        
        with open(req_path, "w") as f:
            f.write("fastapi\n")
        with open(app_path, "w") as f:
            f.write("import fastapi\n")
            
        report_a = evaluate_repo(tmpdirname)
        match = any(f.expected == "FastAPI" and f.category == GapCategory.MATCH for f in report_a.findings)
        assert match, "Test A (MATCH) failed!"
        print("[PASS] Test A: FastAPI explicitly present -> MATCH")
        
        with open(req_path, "w") as f:
            f.write("requests\n")
        os.remove(app_path)
            
        report_b = evaluate_repo(tmpdirname)
        missing = any(f.expected == "FastAPI" and f.category == GapCategory.MISSING for f in report_b.findings)
        assert missing, "Test B (MISSING) failed!"
        print("[PASS] Test B: FastAPI absent + manifest available -> MISSING")
        
        with open(req_path, "w") as f:
            f.write("flask\n")
            
        report_c = evaluate_repo(tmpdirname)
        mismatch = any(f.expected == "FastAPI" and f.category == GapCategory.MISMATCH and f.observed == "Flask" for f in report_c.findings)
        assert mismatch, "Test C (MISMATCH) failed!"
        print("[PASS] Test C: FastAPI replaced by Flask -> MISMATCH")
        
        os.remove(req_path)
        report_d = evaluate_repo(tmpdirname)
        unknown = any(f.expected == "FastAPI" and f.category == GapCategory.UNKNOWN for f in report_d.findings)
        assert unknown, "Test D (UNKNOWN) failed!"
        print("[PASS] Test D: Dependency evidence unavailable -> UNKNOWN")

    print("\nALL 4 M6 ACCEPTANCE TESTS PASSED.")

if __name__ == "__main__":
    test_m6_mutations()
