import os
import sys
from pydantic import ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from idea_refiner.schema import (
    RequirementArtifact,
    PredictionHorizon,
    LatencyRequirement,
    Provenance,
    ProvenanceType,
    QualitativeHorizon,
    TimeUnit,
    ConnectivityType,
    DeploymentTarget
)

def test_valid_qualitative_horizon():
    print("\n--- Testing Valid Qualitative Horizon ---")
    data = {
        "prediction_horizon": {
            "id": "R-01",
            "provenance": {"type": "explicit", "source_quote": "several hours"},
            "qualitative": "several",
            "unit": "hours"
        },
        "latency": {
            "id": "R-02",
            "provenance": {"type": "unknown"}
        },
        "data_freshness": {
            "id": "R-03",
            "provenance": {"type": "unknown"}
        },
        "network": {
            "id": "R-04",
            "provenance": {"type": "unknown"}
        },
        "deployment": {
            "id": "R-05",
            "provenance": {"type": "unknown"}
        }
    }
    
    artifact = RequirementArtifact.model_validate(data)
    assert artifact.prediction_horizon.qualitative == QualitativeHorizon.SEVERAL
    assert artifact.prediction_horizon.exact_value is None
    assert artifact.latency.provenance.type == ProvenanceType.UNKNOWN
    print("Passed: Valid qualitative horizon.")

def test_valid_exact_horizon():
    print("\n--- Testing Valid Exact Horizon ---")
    data = {
        "prediction_horizon": {
            "id": "R-01",
            "provenance": {"type": "explicit", "source_quote": "30 seconds"},
            "exact_value": 30.0,
            "unit": "seconds"
        },
        "latency": {
            "id": "R-02",
            "provenance": {"type": "unknown"}
        },
        "data_freshness": {
            "id": "R-03",
            "provenance": {"type": "unknown"}
        },
        "network": {
            "id": "R-04",
            "provenance": {"type": "unknown"}
        },
        "deployment": {
            "id": "R-05",
            "provenance": {"type": "unknown"}
        }
    }
    artifact = RequirementArtifact.model_validate(data)
    assert artifact.prediction_horizon.exact_value == 30.0
    assert artifact.prediction_horizon.unit == TimeUnit.SECONDS
    print("Passed: Valid exact horizon.")

def test_reject_contradictory_horizon():
    print("\n--- Testing Rejection of Contradictory Horizon ---")
    data = {
        "prediction_horizon": {
            "id": "R-01",
            "provenance": {"type": "explicit", "source_quote": "several hours"},
            "exact_value": 3.0,
            "qualitative": "several",
            "unit": "hours"
        },
        "latency": {
            "id": "R-02",
            "provenance": {"type": "unknown"}
        },
        "data_freshness": {
            "id": "R-03",
            "provenance": {"type": "unknown"}
        },
        "network": {
            "id": "R-04",
            "provenance": {"type": "unknown"}
        },
        "deployment": {
            "id": "R-05",
            "provenance": {"type": "unknown"}
        }
    }
    
    try:
        RequirementArtifact.model_validate(data)
        assert False, "Should have rejected contradictory exact_value and qualitative."
    except ValidationError as e:
        assert "cannot have both exact_value and qualitative set" in str(e)
        print("Passed: Properly rejected contradictory horizon.")

def test_reject_invalid_enum():
    print("\n--- Testing Rejection of Invalid Enum ---")
    data = {
        "prediction_horizon": {
            "id": "R-01",
            "provenance": {"type": "unknown"}
        },
        "latency": {
            "id": "R-02",
            "provenance": {"type": "unknown"}
        },
        "data_freshness": {
            "id": "R-03",
            "provenance": {"type": "unknown"}
        },
        "network": {
            "id": "R-04",
            "provenance": {"type": "explicit", "source_quote": "banana"},
            "connectivity": "banana"
        },
        "deployment": {
            "id": "R-05",
            "provenance": {"type": "unknown"}
        }
    }
    try:
        RequirementArtifact.model_validate(data)
        assert False, "Should have rejected invalid enum 'banana'."
    except ValidationError as e:
        print("Passed: Properly rejected invalid enum 'banana'.")

def test_reject_explicit_when_empty():
    print("\n--- Testing Rejection of EXPLICIT when fields are empty ---")
    data = {
        "prediction_horizon": {
            "id": "R-01",
            "provenance": {"type": "unknown"}
        },
        "latency": {
            "id": "R-02",
            "provenance": {"type": "explicit", "source_quote": "empty"}
        },
        "data_freshness": {
            "id": "R-03",
            "provenance": {"type": "unknown"}
        },
        "network": {
            "id": "R-04",
            "provenance": {"type": "unknown"}
        },
        "deployment": {
            "id": "R-05",
            "provenance": {"type": "unknown"}
        }
    }
    try:
        RequirementArtifact.model_validate(data)
        assert False, "Should have rejected EXPLICIT provenance on empty latency."
    except ValidationError as e:
        assert "Provenance must be UNKNOWN if all values are None" in str(e)
        print("Passed: Properly rejected explicit provenance on empty fields.")

def test_reject_unknown_when_not_empty():
    print("\n--- Testing Rejection of UNKNOWN when fields are populated ---")
    data = {
        "prediction_horizon": {
            "id": "R-01",
            "provenance": {"type": "unknown"}
        },
        "latency": {
            "id": "R-02",
            "provenance": {"type": "unknown"},
            "max_latency_ms": 500
        },
        "data_freshness": {
            "id": "R-03",
            "provenance": {"type": "unknown"}
        },
        "network": {
            "id": "R-04",
            "provenance": {"type": "unknown"}
        },
        "deployment": {
            "id": "R-05",
            "provenance": {"type": "unknown"}
        }
    }
    try:
        RequirementArtifact.model_validate(data)
        assert False, "Should have rejected UNKNOWN provenance when max_latency_ms is set."
    except ValidationError as e:
        assert "Provenance cannot be UNKNOWN if a value is provided" in str(e)
        print("Passed: Properly rejected UNKNOWN provenance when fields have values.")

def test_reject_inference_without_basis():
    print("\n--- Testing Rejection of Inference Without Basis ---")
    data = {
        "prediction_horizon": {"id": "R-01", "provenance": {"type": "unknown"}},
        "latency": {"id": "R-02", "provenance": {"type": "unknown"}},
        "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
        "network": {"id": "R-04", "provenance": {"type": "unknown"}},
        "deployment": {
            "id": "R-05", 
            "provenance": {"type": "inferred", "inference_basis_requirement_ids": []},
            "target": "cloud"
        }
    }
    try:
        RequirementArtifact.model_validate(data)
        assert False, "Should have rejected INFERRED provenance without basis IDs."
    except ValidationError as e:
        assert "INFERRED provenance must include inference_basis_requirement_ids" in str(e)
        print("Passed: Properly rejected inference without basis.")

def test_reject_inference_nonexistent_id():
    print("\n--- Testing Rejection of Inference with Nonexistent ID ---")
    data = {
        "prediction_horizon": {"id": "R-01", "provenance": {"type": "unknown"}},
        "latency": {"id": "R-02", "provenance": {"type": "unknown"}},
        "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
        "network": {"id": "R-04", "provenance": {"type": "unknown"}},
        "deployment": {
            "id": "R-05", 
            "provenance": {"type": "inferred", "inference_basis_requirement_ids": ["R-DOES-NOT-EXIST"]},
            "target": "cloud"
        }
    }
    try:
        RequirementArtifact.model_validate(data)
        assert False, "Should have rejected INFERRED provenance pointing to nonexistent ID."
    except ValidationError as e:
        assert "infers from nonexistent ID" in str(e)
        print("Passed: Properly rejected inference with nonexistent basis ID.")

def test_reject_explicit_missing_quote():
    print("\n--- Testing Rejection of EXPLICIT Missing Quote ---")
    data = {
        "prediction_horizon": {"id": "R-01", "provenance": {"type": "unknown"}},
        "latency": {"id": "R-02", "provenance": {"type": "unknown"}},
        "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
        "network": {"id": "R-04", "provenance": {"type": "unknown"}},
        "deployment": {
            "id": "R-05", 
            "provenance": {"type": "explicit"},
            "target": "cloud"
        }
    }
    try:
        RequirementArtifact.model_validate(data)
        assert False, "Should have rejected EXPLICIT provenance missing source_quote."
    except ValidationError as e:
        assert "EXPLICIT provenance must include a source_quote" in str(e)
        print("Passed: Properly rejected EXPLICIT provenance missing quote.")

def test_reject_invalid_latency():
    print("\n--- Testing Rejection of Invalid Latency (Negative/Zero) ---")
    data = {
        "prediction_horizon": {"id": "R-01", "provenance": {"type": "unknown"}},
        "latency": {
            "id": "R-02", 
            "provenance": {"type": "explicit", "source_quote": "instant"}, 
            "max_latency_ms": -500
        },
        "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
        "network": {"id": "R-04", "provenance": {"type": "unknown"}},
        "deployment": {"id": "R-05", "provenance": {"type": "unknown"}}
    }
    
    try:
        RequirementArtifact.model_validate(data)
        assert False, "Should have rejected negative latency."
    except ValidationError as e:
        assert "strictly greater than 0" in str(e)
    
    data["latency"]["max_latency_ms"] = 0
    try:
        RequirementArtifact.model_validate(data)
        assert False, "Should have rejected zero latency."
    except ValidationError as e:
        assert "strictly greater than 0" in str(e)
        
    print("Passed: Properly rejected invalid latencies.")

def test_reject_duplicate_ids():
    print("\n--- Testing Rejection of Duplicate IDs ---")
    data = {
        "prediction_horizon": {"id": "R-01", "provenance": {"type": "unknown"}},
        "latency": {"id": "R-01", "provenance": {"type": "unknown"}},
        "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
        "network": {"id": "R-04", "provenance": {"type": "unknown"}},
        "deployment": {"id": "R-05", "provenance": {"type": "unknown"}}
    }
    try:
        RequirementArtifact.model_validate(data)
        assert False, "Should have rejected duplicate IDs."
    except ValidationError as e:
        assert "Duplicate requirement ID found" in str(e)
        print("Passed: Properly rejected duplicate IDs.")

if __name__ == "__main__":
    print("==================================================")
    print("      M9.1-A: DETERMINISTIC CONTRACT TESTS        ")
    print("==================================================")
    
    test_valid_qualitative_horizon()
    test_valid_exact_horizon()
    test_reject_contradictory_horizon()
    test_reject_invalid_enum()
    test_reject_explicit_when_empty()
    test_reject_unknown_when_not_empty()
    
    test_reject_inference_without_basis()
    test_reject_inference_nonexistent_id()
    test_reject_explicit_missing_quote()
    test_reject_invalid_latency()
    test_reject_duplicate_ids()
    
    print("\n==================================================")
    print("            ALL CONTRACT TESTS PASSED!            ")
    print("==================================================")
