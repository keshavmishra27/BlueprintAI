import json
import pytest
from pydantic import ValidationError
from idea_refiner.schema import RequirementArtifact

TEST_A_JSON = """
{
  "prediction_horizon": {
    "id": "R-01",
    "provenance": {
      "type": "explicit",
      "source_quote": "several hours in advance"
    },
    "qualitative": "several"
  },
  "latency": {
    "id": "R-02",
    "provenance": {
      "type": "unknown"
    }
  },
  "data_freshness": {
    "id": "R-03",
    "provenance": {
      "type": "explicit",
      "source_quote": "using historical patient-flow data and real-time hospital data"
    },
    "real_time_streams_required": true,
    "historical_data_required": true
  },
  "network": {
    "id": "R-04",
    "provenance": {
      "type": "unknown"
    }
  },
  "deployment": {
    "id": "R-05",
    "provenance": {
      "type": "unknown"
    }
  }
}
"""

TEST_B_JSON = """
{
  "prediction_horizon": {
    "id": "R-01",
    "provenance": {
      "type": "explicit",
      "source_quote": "30 seconds in advance"
    },
    "exact_value": 30.0,
    "unit": "seconds"
  },
  "latency": {
    "id": "R-02",
    "provenance": {
      "type": "unknown"
    }
  },
  "data_freshness": {
    "id": "R-03",
    "provenance": {
      "type": "explicit",
      "source_quote": "continuous ambulance, admission, and triage streams"
    },
    "real_time_streams_required": true
  },
  "network": {
    "id": "R-04",
    "provenance": {
      "type": "unknown"
    }
  },
  "deployment": {
    "id": "R-05",
    "provenance": {
      "type": "unknown"
    }
  }
}
"""

TEST_C_JSON = """
{
  "prediction_horizon": {
    "id": "R-01",
    "provenance": {
      "type": "unknown"
    }
  },
  "latency": {
    "id": "R-02",
    "provenance": {
      "type": "unknown"
    }
  },
  "data_freshness": {
    "id": "R-03",
    "provenance": {
      "type": "unknown"
    }
  },
  "network": {
    "id": "R-04",
    "provenance": {
      "type": "explicit",
      "source_quote": "without internet connectivity"
    },
    "connectivity": "offline"
  },
  "deployment": {
    "id": "R-05",
    "provenance": {
      "type": "explicit",
      "source_quote": "on-device ... low-end phones"
    },
    "target": "on_device",
    "hardware_profile": "consumer_mobile"
  }
}
"""

MALFORMED_EXPLICIT_NO_QUOTE = """
{
  "prediction_horizon": {
    "id": "R-01",
    "provenance": {
      "type": "explicit"
    },
    "qualitative": "several"
  },
  "latency": {"id": "R-02", "provenance": {"type": "unknown"}},
  "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
  "network": {"id": "R-04", "provenance": {"type": "unknown"}},
  "deployment": {"id": "R-05", "provenance": {"type": "unknown"}}
}
"""

MALFORMED_UNKNOWN_WITH_VALUE = """
{
  "prediction_horizon": {
    "id": "R-01",
    "provenance": {
      "type": "unknown"
    }
  },
  "latency": {
    "id": "R-02",
    "provenance": {
      "type": "unknown"
    },
    "max_latency_ms": 500
  },
  "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
  "network": {"id": "R-04", "provenance": {"type": "unknown"}},
  "deployment": {"id": "R-05", "provenance": {"type": "unknown"}}
}
"""

MALFORMED_INFERRED_NO_BASIS = """
{
  "prediction_horizon": {
    "id": "R-01",
    "provenance": {
      "type": "inferred"
    },
    "qualitative": "several"
  },
  "latency": {"id": "R-02", "provenance": {"type": "unknown"}},
  "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
  "network": {"id": "R-04", "provenance": {"type": "unknown"}},
  "deployment": {"id": "R-05", "provenance": {"type": "unknown"}}
}
"""

MALFORMED_DUPLICATE_IDS = """
{
  "prediction_horizon": {
    "id": "R-01",
    "provenance": {"type": "unknown"}
  },
  "latency": {
    "id": "R-01", 
    "provenance": {"type": "unknown"}
  },
  "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
  "network": {"id": "R-04", "provenance": {"type": "unknown"}},
  "deployment": {"id": "R-05", "provenance": {"type": "unknown"}}
}
"""

MALFORMED_EXACT_AND_QUALITATIVE = """
{
  "prediction_horizon": {
    "id": "R-01",
    "provenance": {
      "type": "explicit",
      "source_quote": "several hours, exactly 5"
    },
    "exact_value": 5,
    "qualitative": "several"
  },
  "latency": {"id": "R-02", "provenance": {"type": "unknown"}},
  "data_freshness": {"id": "R-03", "provenance": {"type": "unknown"}},
  "network": {"id": "R-04", "provenance": {"type": "unknown"}},
  "deployment": {"id": "R-05", "provenance": {"type": "unknown"}}
}
"""

def test_valid_payload_a():
    artifact = RequirementArtifact.model_validate_json(TEST_A_JSON)
    assert artifact.prediction_horizon.qualitative == "several"
    assert artifact.data_freshness.real_time_streams_required is True

def test_valid_payload_b():
    artifact = RequirementArtifact.model_validate_json(TEST_B_JSON)
    assert artifact.prediction_horizon.exact_value == 30.0
    assert artifact.latency.provenance.type == "unknown"
    assert artifact.latency.max_latency_ms is None
    assert artifact.data_freshness.real_time_streams_required is True

def test_valid_payload_c():
    artifact = RequirementArtifact.model_validate_json(TEST_C_JSON)
    assert artifact.network.connectivity == "offline"
    assert artifact.deployment.target == "on_device"

def test_malformed_explicit_no_quote():
    with pytest.raises(ValidationError) as exc_info:
        RequirementArtifact.model_validate_json(MALFORMED_EXPLICIT_NO_QUOTE)
    assert "EXPLICIT provenance must include a source_quote" in str(exc_info.value)

def test_malformed_unknown_with_value():
    with pytest.raises(ValidationError) as exc_info:
        RequirementArtifact.model_validate_json(MALFORMED_UNKNOWN_WITH_VALUE)
    assert "Provenance cannot be UNKNOWN if a value is provided" in str(exc_info.value)

def test_malformed_inferred_no_basis():
    with pytest.raises(ValidationError) as exc_info:
        RequirementArtifact.model_validate_json(MALFORMED_INFERRED_NO_BASIS)
    assert "INFERRED provenance must include inference_basis_requirement_ids" in str(exc_info.value)

def test_malformed_duplicate_ids():
    with pytest.raises(ValidationError) as exc_info:
        RequirementArtifact.model_validate_json(MALFORMED_DUPLICATE_IDS)
    assert "Duplicate requirement ID found" in str(exc_info.value)

def test_malformed_exact_and_qualitative():
    with pytest.raises(ValidationError) as exc_info:
        RequirementArtifact.model_validate_json(MALFORMED_EXACT_AND_QUALITATIVE)
    assert "PredictionHorizon cannot have both exact_value and qualitative set" in str(exc_info.value)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
