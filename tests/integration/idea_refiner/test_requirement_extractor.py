import os
import sys
import pytest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from idea_refiner.parsers.providers.groq import GroqProvider
from idea_refiner.parsers.requirement_extractor import RequirementExtractor
from idea_refiner.schema import ProvenanceType, QualitativeHorizon, TimeUnit, ConnectivityType, DeploymentTarget, HardwareProfile
from dotenv import load_dotenv

pytestmark = pytest.mark.skip(reason="Live LLM Integration Test. Run manually when API keys are configured.")

@pytest.fixture
def extractor():
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
    provider = GroqProvider(model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"))
    return RequirementExtractor(provider)

def test_hospital_a(extractor):
    idea = "Hospital overcrowding prediction several hours in advance using historical patient-flow data and real-time hospital data."
    artifact = extractor.extract_requirements(idea)
    
    assert artifact.prediction_horizon.exact_value is None, "Should not invent precision"
    assert artifact.prediction_horizon.qualitative == QualitativeHorizon.SEVERAL, "Should capture qualitative 'several'"
    assert artifact.prediction_horizon.unit == TimeUnit.HOURS, "Unit should be hours"
    assert artifact.prediction_horizon.provenance.type == ProvenanceType.EXPLICIT, "Horizon should be explicit"
    
    assert artifact.latency.max_latency_ms is None, "Should not invent latency"
    assert artifact.latency.provenance.type == ProvenanceType.UNKNOWN, "Latency provenance should be UNKNOWN"
    
    assert artifact.network.connectivity is None, "Should not invent network connectivity"
    assert artifact.network.provenance.type == ProvenanceType.UNKNOWN, "Network provenance should be UNKNOWN"

def test_hospital_a_counterfactual_30s(extractor):
    idea = "Hospital emergency response system predicting overcrowding 30 seconds in advance using historical patient-flow data and real-time hospital data."
    artifact = extractor.extract_requirements(idea)
    
    assert artifact.prediction_horizon.exact_value == 30.0, "Should extract exactly 30"
    assert artifact.prediction_horizon.unit == TimeUnit.SECONDS, "Unit should be seconds"
    assert artifact.latency.provenance.type == ProvenanceType.UNKNOWN, "Latency should still be unknown"

def test_hospital_a_counterfactual_30s_latency(extractor):
    idea = "Hospital emergency response system predicting overcrowding 30 seconds in advance from continuous ambulance, admission, and triage streams, with extremely low alert latency."
    artifact = extractor.extract_requirements(idea)
    
    assert artifact.prediction_horizon.exact_value == 30.0, "Should extract exactly 30"
    assert artifact.latency.provenance.type in (ProvenanceType.EXPLICIT, ProvenanceType.INFERRED), "Latency provenance should no longer be UNKNOWN"

def test_mobile_c(extractor):
    idea = "Offline mobile application performing image classification on-device without internet connectivity on low-end phones."
    artifact = extractor.extract_requirements(idea)
    
    assert artifact.network.connectivity == ConnectivityType.OFFLINE, "Should extract OFFLINE"
    assert artifact.deployment.target == DeploymentTarget.ON_DEVICE, "Should extract ON_DEVICE"
    assert artifact.deployment.hardware_profile in (HardwareProfile.CONSUMER_MOBILE, HardwareProfile.LOW_POWER_IOT), "Should extract low-end profile"

if __name__ == "__main__":
    print("This is an integration test. Run via pytest: pytest tests/integration/idea_refiner/test_requirement_extractor.py")
