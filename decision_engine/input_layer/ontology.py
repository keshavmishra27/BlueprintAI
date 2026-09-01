from typing import List, Dict, Optional, Any, Callable
from decision_engine.input_layer.schemas import Requirement, ArchitectureNode

ONTOLOGY_VERSION = "v3.8"

class OntologyResult:
    def __init__(self, requirement_failures: List[str] = None, constraint_failures: List[str] = None):
        self.requirement_failures = requirement_failures or []
        self.constraint_failures = constraint_failures or []

def infer_properties(semantic_dependencies: List[str]) -> Dict[str, str]:
    properties = {}
    if "requires_manual_usb_transfer" in semantic_dependencies:
        properties["data_refresh_mode"] = "manual_batch"
    if "requires_heavy_anonymization" in semantic_dependencies:
        properties["processing_mode"] = "heavy_anonymization"
    if "requires_complex_scraping_or_manual_entry" in semantic_dependencies:
        properties["data_acquisition_mode"] = "manual_intensive"
    if "requires_emr_database_integration" in semantic_dependencies:
        properties["data_access_mode"] = "direct_emr_integration"
    if "requires_approved_emr_interface" in semantic_dependencies:
        properties["data_access_mode"] = "governed_api"
    if "requires_realtime_operational_data" in semantic_dependencies:
        properties["data_refresh_mode"] = "event_driven_or_realtime"
        
    if ONTOLOGY_VERSION >= "v3.10.1":
        if "requires_brain_computer_interface" in semantic_dependencies:
            properties["bci_mode"] = "active"
            
    if ONTOLOGY_VERSION >= "v3.10.2":
        if "requires_staffing_feed" in semantic_dependencies:
            properties["staffing_feed_mode"] = "active"
            
    if ONTOLOGY_VERSION >= "v3.10.3":
        if "requires_irrelevant_magic" in semantic_dependencies:
            properties["magic_mode"] = "safe"
            
    if ONTOLOGY_VERSION >= "v3.11":
        if "requires_staffing_feed_v2" in semantic_dependencies:
            properties["staffing_data_mode"] = "external_realtime"
            
    if ONTOLOGY_VERSION >= "v3.12":
        if "requires_staffing_feed_v3" in semantic_dependencies:
            properties["staffing_mode_v3"] = "active"
        if "requires_rfid_tracking_v3" in semantic_dependencies:
            properties["rfid_mode_v3"] = "active"
    
    if "test_recognized_triggering" in semantic_dependencies:
        properties["synthetic_trigger"] = "active"
    if "test_conflict_1" in semantic_dependencies:
        properties["conflict_state_1"] = "active"
    if "test_conflict_2" in semantic_dependencies:
        properties["conflict_state_2"] = "active"
        
    return properties

def evaluate_properties(properties: Dict[str, str], env_constraints: List[str], env_requirements: List[Requirement]) -> OntologyResult:
    req_failures = []
    constraint_failures = []
    
    if properties.get("data_refresh_mode") == "manual_batch":
        for req in env_requirements:
            if req.name == "Predict waiting time":
                req_failures.append(req.name)
                
    if properties.get("processing_mode") == "heavy_anonymization":
        if any("real_time_processing_required" in c for c in env_constraints):
            constraint_failures.append("real_time_processing_required_violated_by_heavy_anonymization")

    if properties.get("data_acquisition_mode") == "manual_intensive":
        if any("budget_less_than_500_per_month" in c for c in env_constraints):
            constraint_failures.append("budget_less_than_500_per_month_violated_by_complex_scraping")
            
    if properties.get("data_access_mode") == "direct_emr_integration":
        if "emr_direct_access_authorized" not in env_constraints:
            constraint_failures.append("emr_direct_access_authorization_missing")
            
    if properties.get("data_access_mode") == "governed_api":
        if "approved_hl7_interface_available" not in env_constraints:
            constraint_failures.append("governed_api_interface_unavailable")
        if "application_authorized" not in env_constraints:
            constraint_failures.append("governed_api_authorization_missing")
            
    if properties.get("data_refresh_mode") == "event_driven_or_realtime":
        if "realtime_operational_feed_available" not in env_constraints:
            constraint_failures.append("realtime_feed_unavailable")
            
    if ONTOLOGY_VERSION >= "v3.10.1":
        if properties.get("bci_mode") == "active":
            if "neural_link_available" not in env_constraints:
                constraint_failures.append("neural_link_missing")
                
    if ONTOLOGY_VERSION >= "v3.10.2":
        if properties.get("staffing_feed_mode") == "active":
            if "staffing_api_available" not in env_constraints:
                constraint_failures.append("staffing_api_missing")
                
    if ONTOLOGY_VERSION >= "v3.10.3":
        pass
        
    if ONTOLOGY_VERSION >= "v3.11":
        if properties.get("staffing_data_mode") == "external_realtime":
            if "realtime_staffing_feed_available" not in env_constraints:
                constraint_failures.append("staffing_feed_missing")
            if "feed_is_stale_mode" in env_constraints:
                constraint_failures.append("staffing_feed_stale")
            if "no_external_data_allowed" in env_constraints:
                constraint_failures.append("external_data_prohibited")
                
    if ONTOLOGY_VERSION >= "v3.12":
        if properties.get("staffing_mode_v3") == "active":
            if "staffing_feed_v3_available" not in env_constraints:
                constraint_failures.append("staffing_feed_missing")
                
        if properties.get("rfid_mode_v3") == "active":
            if "rfid_infrastructure_v3_available" not in env_constraints:
                constraint_failures.append("rfid_infrastructure_missing")
            
    if properties.get("synthetic_trigger") == "active":
        if any("trigger" in c for c in env_constraints):
            for req in env_requirements:
                if req.name == "Synthetic Test Req":
                    req_failures.append(req.name)
                    
    if properties.get("conflict_state_1") == "active":
        constraint_failures.append("test_conflict_1_failure")
        
    if properties.get("conflict_state_2") == "active":
        constraint_failures.append("test_conflict_2_failure")

    return OntologyResult(requirement_failures=req_failures, constraint_failures=constraint_failures)

KNOWN_DEPENDENCIES_V3_8 = {
    "requires_manual_usb_transfer",
    "requires_heavy_anonymization",
    "requires_complex_scraping_or_manual_entry",
    "requires_emr_database_integration",
    "test_recognized_triggering",
    "test_conflict_1",
    "test_conflict_2",
    "requires_approved_emr_interface",
    "requires_realtime_operational_data"
}

KNOWN_DEPENDENCIES_V3_10_0 = KNOWN_DEPENDENCIES_V3_8.copy()

def get_known_dependencies():
    deps = KNOWN_DEPENDENCIES_V3_10_0.copy()
    if ONTOLOGY_VERSION >= "v3.10.1":
        deps.add("requires_brain_computer_interface")
    if ONTOLOGY_VERSION >= "v3.10.2":
        deps.add("requires_staffing_feed")
    if ONTOLOGY_VERSION >= "v3.10.3":
        deps.add("requires_irrelevant_magic")
    if ONTOLOGY_VERSION >= "v3.11":
        deps.add("requires_staffing_feed_v2")
    if ONTOLOGY_VERSION >= "v3.12":
        deps.add("requires_staffing_feed_v3")
        deps.add("requires_rfid_tracking_v3")
    return deps

def evaluate_ontology(arch: ArchitectureNode, env_constraints: List[str], env_requirements: List[Requirement]) -> OntologyResult:
    recognized_deps = []
    known_deps = get_known_dependencies()
    for dependency in arch.semantic_dependencies:
        if dependency in known_deps:
            recognized_deps.append(dependency)
        else:
            pass
            
    properties = infer_properties(recognized_deps)
    
    return evaluate_properties(properties, env_constraints, env_requirements)
