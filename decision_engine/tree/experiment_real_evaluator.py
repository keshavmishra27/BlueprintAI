import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement
from decision_engine.input_layer.evaluator import check_violations, evaluate_battle

def run_unit_tests():
    print("=== UNIT TESTS ===")
    
    arch1 = ArchitectureNode(
        inputs=[], processing=["Small Local Classifier"], decision=[], output=[], capabilities=[], 
        data_required=["local_data"], resources_required=["CPU"], constraints=[]
    )
    v1 = check_violations(arch1, ["no_gpu"])
    print(f"Test 1 (CPU vs no_gpu): {'PASS' if len(v1)==0 else 'FAIL - ' + str(v1)}")
    
    arch2 = ArchitectureNode(
        inputs=[], processing=["Small Local Classifier"], decision=[], output=[], capabilities=[], 
        data_required=["local_data"], resources_required=["GPU"], constraints=[]
    )
    v2 = check_violations(arch2, ["no_gpu"])
    print(f"Test 2 (GPU vs no_gpu): {'FAIL' if len(v2)>0 else 'PASS'}")

    arch3 = ArchitectureNode(
        inputs=[], processing=["Cloud LLM API"], decision=[], output=[], capabilities=[], 
        data_required=["live_data"], resources_required=["API"], constraints=[]
    )
    v3 = check_violations(arch3, ["no_historical_data"])
    print(f"Test 3 (Cloud LLM/live_data vs no_historical_data): {'PASS' if len(v3)==0 else 'FAIL - ' + str(v3)}")
    
    arch4 = ArchitectureNode(
        inputs=[], processing=["Predictive ML Model"], decision=[], output=[], capabilities=[], 
        data_required=["historical_patient_data"], resources_required=["GPU"], constraints=[]
    )
    v4 = check_violations(arch4, ["no_historical_data"])
    print(f"Test 4 (ML/historical vs no_historical_data): {'FAIL' if len(v4)>0 else 'PASS'}")
    print()

def get_architectures():
    return {
        "Hospital": {
            "constraints": ["no_historical_data", "hospital intranet available"],
            "requirements": [Requirement(name="reduce waiting time", required=True)],
            "a_baseline": ArchitectureNode(
                inputs=[], processing=["Cloud LLM Prediction"], decision=[], output=[], capabilities=[], 
                data_required=["historical_patient_data"], resources_required=["Cloud API"], constraints=[]
            ),
            "b_baseline": ArchitectureNode(
                inputs=[], processing=["Rule-based Triage"], decision=[], output=[], capabilities=[], 
                data_required=["live_queue_data"], resources_required=["Local Server"], constraints=[]
            ),
            "blueprint": ArchitectureNode(
                inputs=[], processing=["Rule-based Triage"], decision=[], output=[], capabilities=[], 
                data_required=["live_queue_data"], resources_required=["Local Server"], constraints=[]
            )
        },
        "Crop": {
            "constraints": ["no_cloud", "intermittent connectivity"],
            "requirements": [Requirement(name="disease detection", required=True)],
            "a_baseline": ArchitectureNode(
                inputs=[], processing=["Edge AI Sync"], decision=[], output=[], capabilities=[], 
                data_required=["image_data"], resources_required=["Local Edge Device"], constraints=[]
            ),
            "b_baseline": ArchitectureNode(
                inputs=[], processing=["Edge AI"], decision=[], output=[], capabilities=[], 
                data_required=["image_data"], resources_required=["Local Edge Device"], constraints=[]
            ),
            "blueprint": ArchitectureNode(
                inputs=[], processing=["Edge AI", "SMS Alerts"], decision=[], output=[], capabilities=[], 
                data_required=["image_data"], resources_required=["Local Edge Device", "Cellular"], constraints=[]
            )
        },
        "Traffic": {
            "constraints": ["low bandwidth", "strict budget"],
            "requirements": [Requirement(name="reduce congestion", required=True)],
            "a_baseline": ArchitectureNode(
                inputs=[], processing=["Cloud AI Traffic Analysis"], decision=[], output=[], capabilities=[], 
                data_required=["live video stream"], resources_required=["Cloud Compute"], constraints=[]
            ),
            "b_baseline": ArchitectureNode(
                inputs=[], processing=["Upgrade to smart cameras"], decision=[], output=[], capabilities=[], 
                data_required=["video"], resources_required=["High Budget Hardware"], constraints=[]
            ),
            "blueprint": ArchitectureNode(
                inputs=[], processing=["Local Radar/IR Sensors", "Local Controller"], decision=[], output=[], capabilities=[], 
                data_required=["sensor_pulses"], resources_required=["Low Cost Sensors", "Edge Controller"], constraints=[]
            )
        },
        "Education": {
            "constraints": ["no_external_storage", "strict privacy"],
            "requirements": [Requirement(name="personalized tutoring", required=True)],
            "a_baseline": ArchitectureNode(
                inputs=[], processing=["Encrypted Centralized Cloud Storage"], decision=[], output=[], capabilities=[], 
                data_required=["student_history"], resources_required=["Cloud Database"], constraints=[]
            ),
            "b_baseline": ArchitectureNode(
                inputs=[], processing=["Local On-Device Storage"], decision=[], output=[], capabilities=[], 
                data_required=["student_history"], resources_required=["Tablet Storage"], constraints=[]
            ),
            "blueprint": ArchitectureNode(
                inputs=[], processing=["Local Storage", "Federated Weight Updates"], decision=[], output=[], capabilities=["autonomous learning"], 
                data_required=["student_history"], resources_required=["Tablet Storage", "Network"], constraints=[]
            )
        },
        "Waste": {
            "constraints": ["no_power_source", "limited_network"],
            "requirements": [Requirement(name="optimize routing", required=True)],
            "a_baseline": ArchitectureNode(
                inputs=[], processing=["Solar LoRaWAN"], decision=[], output=[], capabilities=[], 
                data_required=["fill_level"], resources_required=["Solar Panel", "LoRaWAN"], constraints=[]
            ),
            "b_baseline": ArchitectureNode(
                inputs=[], processing=["Battery LoRaWAN"], decision=[], output=[], capabilities=[], 
                data_required=["fill_level"], resources_required=["Battery", "LoRaWAN"], constraints=[]
            ),
            "blueprint": ArchitectureNode(
                inputs=[], processing=["Battery LoRaWAN"], decision=[], output=[], capabilities=[], 
                data_required=["fill_level"], resources_required=["Battery", "LoRaWAN"], constraints=[]
            )
        },
        "Disaster": {
            "constraints": ["offline", "cellular_down"],
            "requirements": [Requirement(name="coordinate rescue", required=True)],
            "a_baseline": ArchitectureNode(
                inputs=[], processing=["Offline app wait for network"], decision=[], output=[], capabilities=[], 
                data_required=["gps"], resources_required=["Internet"], constraints=[]
            ),
            "b_baseline": ArchitectureNode(
                inputs=[], processing=["Mesh networking"], decision=[], output=[], capabilities=[], 
                data_required=["gps"], resources_required=["Bluetooth/Wi-Fi Direct"], constraints=[]
            ),
            "blueprint": ArchitectureNode(
                inputs=[], processing=["Mesh networking"], decision=[], output=[], capabilities=[], 
                data_required=["gps"], resources_required=["Bluetooth/Wi-Fi Direct"], constraints=[]
            )
        },
        "Cybersecurity": {
            "constraints": ["no_external_storage", "no_gpu"],
            "requirements": [Requirement(name="phishing detection", required=True)],
            "a_baseline": ArchitectureNode(
                inputs=[], processing=["On-Premise Local LLM"], decision=[], output=[], capabilities=[], 
                data_required=["emails"], resources_required=["GPU"], constraints=[]
            ),
            "b_baseline": ArchitectureNode(
                inputs=[], processing=["YARA Rules", "Small CPU Classifier"], decision=[], output=[], capabilities=[], 
                data_required=["emails"], resources_required=["CPU"], constraints=[]
            ),
            "blueprint": ArchitectureNode(
                inputs=[], processing=["Local Rule-based filtering"], decision=[], output=[], capabilities=[], 
                data_required=["emails"], resources_required=["CPU"], constraints=[]
            )
        },
        "AgLogistics": {
            "constraints": ["feature_phones_only"],
            "requirements": [Requirement(name="match buyers", required=True)],
            "a_baseline": ArchitectureNode(
                inputs=[], processing=["USSD/SMS matching"], decision=[], output=[], capabilities=[], 
                data_required=["crop_price"], resources_required=["Telecom API"], constraints=[]
            ),
            "b_baseline": ArchitectureNode(
                inputs=[], processing=["USSD/SMS matching"], decision=[], output=[], capabilities=[], 
                data_required=["crop_price"], resources_required=["Telecom API"], constraints=[]
            ),
            "blueprint": ArchitectureNode(
                inputs=[], processing=["USSD/SMS matching", "IVR"], decision=[], output=[], capabilities=[], 
                data_required=["crop_price"], resources_required=["Telecom API", "IVR System"], constraints=[]
            )
        }
    }

def run_experiment_1():
    run_unit_tests()
    domains = get_architectures()
    
    print("=== EXPERIMENT 1: ARCHITECTURE EVALUATIONS ===\n")
    
    for d_name, d_data in domains.items():
        print(f"DOMAIN: {d_name}")
        print(f"Constraints: {d_data['constraints']}")
        
        for arch_type in ["a_baseline", "b_baseline", "blueprint"]:
            arch = d_data[arch_type]
            v = check_violations(arch, d_data['constraints'])
            feasible = len(v) == 0
            
            print(f"  {arch_type.upper():<12}: Feasible? {str(feasible):<5} | Violations: {v}")
            
        print("-" * 50)

if __name__ == "__main__":
    run_experiment_1()
