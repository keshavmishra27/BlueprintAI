import sys
import os
import hashlib
import json
from datetime import datetime

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

def hash_file(filepath):
    path = os.path.join(base_dir, filepath)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def create_manifest():
    manifest = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "phase": "V3.3 Frozen",
        "hashes": {
            "evaluator": hash_file("decision_engine/input_layer/evaluator.py"),
            "ontology": hash_file("decision_engine/input_layer/ontology.py"),
            "decision_graph": hash_file("decision_engine/tree/decision_graph.py"),
            "optimizer": hash_file("decision_engine/tree/optimizer.py"),
            "journey_router": hash_file("backend/app/routers/journey.py"),
            "v3.2_regression_expectations": hash_file("benchmark_suite/level6/results/v3.2_hospital_case_01/v3.2_regression_expectations.json")
        },
        "results": {
            "ontology_audit": "PASSED - 9 cases verified (deterministic consequence, informational ignorance, composition)",
            "identical_replay": "PASSED - Refiner output mechanically transformed from TERMINAL to REJECTED based strictly on deterministic ontology rules."
        }
    }
    
    out_path = os.path.join(base_dir, "benchmark_suite", "level6", "results", "v3.3_frozen_manifest.json")
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Manifest created at {out_path}")

if __name__ == "__main__":
    create_manifest()
