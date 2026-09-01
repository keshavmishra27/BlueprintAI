import httpx
import json
import sys

base_url = "http://127.0.0.1:8089"

def build_arch_node(processing, capabilities=None, semantic_deps=None, data=None, resources=None, constraints=None, historical_decisions=None):
    return {
        "inputs": ["Data input"],
        "processing": processing,
        "decision": ["Logic decision"],
        "output": ["System Output"],
        "capabilities": capabilities or [],
        "semantic_dependencies": semantic_deps or [],
        "data_required": data or [],
        "resources_required": resources or [],
        "constraints": constraints or [],
        "historical_decisions": historical_decisions or []
    }

def print_eval(player_name, arch_node, battle_info, is_a=False):
    violations = battle_info["a_constraint_violations"] if is_a else battle_info["b_constraint_violations"]
    feasible = battle_info["a_feasible"] if is_a else battle_info["b_feasible"]
    reqs_met = []
    for req in battle_info["requirement_evaluations"]:
        sat = req["user_satisfies"] if is_a else req["player_b_satisfies"]
        if sat: reqs_met.append(req["requirement"])
        
    print(f"#### {player_name}")
    print(f"- **Architecture Name:** `{' -> '.join(arch_node['processing'])}`")
    print(f"- **Capabilities:** {', '.join(arch_node['capabilities']) or 'None'}")
    print(f"- **Data Required:** {', '.join(arch_node['data_required']) or 'None'}")
    print(f"- **Resources Required:** {', '.join(arch_node['resources_required']) or 'None'}")
    print(f"- **Requirements Met:** {', '.join(reqs_met) or 'None'}")
    print(f"- **Constraint Violations:**")
    if not violations:
        print("  - None")
    else:
        for v in violations:
            print(f"  - {v}")
    print(f"- **Feasible?** {feasible}\n")

def run_test(test_name, payload, answer_sequence=None):
    print(f"## {test_name}\n")
    print(f"**WHAT:** {payload['what']}")
    print(f"**WHY:** {payload['why']}")
    print(f"**CONSTRAINTS:** {', '.join(payload['constraints'])}\n")
    
    print("### Raw Agent Payload")
    print("```json\n" + json.dumps(payload, indent=2) + "\n```\n")
    
    r = httpx.post(f"{base_url}/api/journey/start", json=payload, timeout=10.0)
    if r.status_code != 200:
        print(f"**API ERROR {r.status_code}:** {r.text}\n")
        return
        
    resp = r.json()
    battle = resp["current_battle_result"] if "current_battle_result" in resp else resp.get("tree_state", {}).get("battle_history", [{}])[-1]
    
    print("### Battle Results (Gemini Baseline vs Evidence-Guided Candidate)\n")
    
    print_eval("Gemini Baseline (Player A)", payload["gemini_baseline_architecture"], battle, is_a=True)
    print_eval("Evidence-Guided Candidate (Player B)", payload["player_b_architecture"], battle, is_a=False)
    
    print(f"**WINNER:** {battle.get('winner', 'unknown')} ({battle.get('reasoning', '')})\n")
    
    if resp["is_complete"]:
        print("### Conclusion")
        print("Journey finished. No uncertainties to explore.")
        if not battle.get("a_feasible") and not battle.get("b_feasible"):
            print("**NO_FEASIBLE_CANDIDATE_ARCHITECTURE_FOUND**\n")
        return
        
    q_node = resp["current_question"]
    print("### Branch Candidate Impact Analysis\n")
    print(f"**Selected Uncertainty:** {q_node['question_text']}")
    print(f"**Impact Score:** {resp.get('decision_impact', q_node['uncertainty']['decision_impact_score'])}\n")
    print("---\n")
    
    if answer_sequence:
        for ans_info in answer_sequence:
            r_fresh = httpx.post(f"{base_url}/api/journey/start", json=payload, timeout=10.0)
            if r_fresh.status_code != 200:
                print(f"**API ERROR {r_fresh.status_code}:** {r_fresh.text}\n")
                break
                
            resp_fresh = r_fresh.json()
            real_session_id = resp_fresh.get("session_id")
            
            ans = ans_info["answer"]
            new_arch = ans_info.get("new_player_b_architecture")
            new_uncs = ans_info.get("new_uncertainties", [])
            print(f"### Exploring Branch: {ans} for '{q_node['question_text']}'\n")
            
            ans_payload = {
                "session_id": real_session_id,
                "selected_option": ans,
                "new_player_b_architecture": new_arch,
                "new_uncertainties": new_uncs
            }
            
            r2 = httpx.post(f"{base_url}/api/journey/answer", json=ans_payload, timeout=10.0)
            if r2.status_code != 200:
                print(f"**API ERROR {r2.status_code}:** {r2.text}\n")
                return
                
            resp2 = r2.json()
            battle2 = resp2["current_battle_result"]
            
            print_eval(f"Adapted Player B", new_arch or payload["player_b_architecture"], battle2, is_a=False)
            print(f"**WINNER:** {battle2.get('winner')} ({battle2.get('reasoning')})\n")
            
            if resp2["is_complete"]:
                if not battle2.get("b_feasible"):
                    print("**Branch Failed Constraints/Requirements**\n")
                continue
                
            q_node = resp2["current_question"]
            print("### Branch Candidate Impact Analysis\n")
            print(f"**Next Uncertainty:** {q_node['question_text']}\n")
            print("---\n")
            
        print("### Conclusion")
        print("Search space exhausted.")
        print("**ALL FEASIBLE BRANCHES EXHAUSTED**")
        print("**NO_FEASIBLE_CANDIDATE_ARCHITECTURE_FOUND**\n")

def run_all():
    print("# Decision Engine Validation Tests\n")
    
    test_a = {
        "what": "Automatically mark classroom attendance.",
        "why": "Manual attendance takes too much class time.",
        "how": "Students scan a QR code and the system verifies their presence.",
        "constraints": ["50 students", "45-minute class", "no paid APIs", "Android phones", "unreliable internet"],
        "requirements": [{"name": "Mark classroom attendance", "required": True}],
        "gemini_baseline_architecture": build_arch_node(
            processing=["Cloud API Image Recognition", "Cloud Database Sync"],
            capabilities=["facial recognition attendance", "cloud storage"],
            semantic_deps=["paid_api", "commercial_cloud", "requires_cloud"],
            data=["high resolution images"],
            resources=["Paid API", "Commercial Cloud Service"]
        ),
        "player_b_architecture": build_arch_node(
            processing=["Local QR Code Generation", "Bluetooth/Wi-Fi Direct Sync", "Periodic Cloud Upload"],
            capabilities=["qr code attendance", "offline sync", "presence detection"],
            semantic_deps=[],
            data=["local student IDs"],
            resources=["Local Server", "Android devices"],
            historical_decisions=[
                {
                    "historical_decision": "Use Local QR Code Generation and Offline Sync",
                    "historical_evidence": {
                        "source_project": "SIH 2022 Local Attendance",
                        "evidence_pattern": "On-device processing removes dependence on continuous connectivity.",
                        "why_it_worked": "Allowed attendance marking to proceed uninterrupted during network outages.",
                        "applicability": "Useful when deployment has intermittent connectivity."
                    },
                    "decision_status": "adopt",
                    "reasoning": "Intermittent connectivity is a core constraint here, making this pattern highly applicable."
                }
            ]
        ),
        "uncertainties": [
            {
                "id": "unc-local-server",
                "question_text": "Is a local server permanently available in the classroom?",
                "question_target": "Local Server",
                "unknown_fact": "Local server availability",
                "importance": "High",
                "yes_mutation": {"add_constraints": ["local server available"], "remove_constraints": []},
                "no_mutation": {"add_constraints": ["no local server"], "remove_constraints": []},
                "yes_candidate_architecture": build_arch_node(
                    processing=["Local Server Auth", "Wi-Fi Direct Sync"],
                    capabilities=["qr code attendance", "offline sync", "presence detection"],
                    semantic_deps=[],
                    data=["local student IDs"],
                    resources=["Local Server", "Android devices"]
                ),
                "no_candidate_architecture": build_arch_node(
                    processing=["Teacher Phone Master Auth", "Bluetooth Mesh Sync"],
                    capabilities=["qr code attendance", "offline sync", "presence detection"],
                    semantic_deps=[],
                    data=["local student IDs"],
                    resources=["Teacher Android device", "Student Android devices"]
                )
            }
        ]
    }
    
    test_b = {
        "what": "Reduce unnecessary garbage-collection trips.",
        "why": "Trucks visit bins that aren't full.",
        "how": "Use sensors to tell the truck when a bin needs collection.",
        "constraints": ["limited battery", "poor connectivity", "48-hour prototype"],
        "requirements": [{"name": "Optimize waste collection", "required": True}],
        "gemini_baseline_architecture": build_arch_node(
            processing=["Continuous Video Stream", "Cloud ML Fill Detection", "Real-time Routing"],
            capabilities=["real-time waste monitoring", "dynamic routing"],
            semantic_deps=["continuous_streaming", "requires_cloud", "requires_camera"],
            data=["continuous streaming video", "GPS data"],
            resources=["Video cameras", "Cloud Servers", "High bandwidth 5G"]
        ),
        "player_b_architecture": build_arch_node(
            processing=["Ultrasonic Fill Sensor", "Edge Threshold Trigger", "LoRaWAN periodic update", "Daily Route Gen"],
            capabilities=["fill level sensor monitoring", "dynamic routing"],
            semantic_deps=[],
            data=["low bandwidth sensor pings"],
            resources=["Arduino/Ultrasonic sensors", "LoRaWAN Gateway", "Basic laptop"],
            historical_decisions=[
                {
                    "historical_decision": "Use Edge Threshold Triggers via LoRaWAN",
                    "historical_evidence": {
                        "source_project": "Smart Bin 2021",
                        "evidence_pattern": "Transmit only state changes instead of raw sensor streams.",
                        "why_it_worked": "Reduced battery consumption by 90% and functioned on low-bandwidth networks.",
                        "applicability": "Crucial for limited battery and poor connectivity environments."
                    },
                    "decision_status": "adopt",
                    "reasoning": "Both battery and connectivity are heavily constrained in this environment."
                }
            ]
        ),
        "uncertainties": []
    }
    
    test_c = {
        "what": "Help students identify topics they are weak in.",
        "why": "Students don't know what to practice.",
        "how": "Analyze their previous practice and recommend questions.",
        "constraints": ["no external storage", "student data must stay locally", "basic laptop", "48-hour prototype"],
        "requirements": [{"name": "Help identify topics they are weak in", "required": True}],
        "gemini_baseline_architecture": build_arch_node(
            processing=["Upload student history", "OpenAI GPT-4 Analysis", "Generate Recommendations"],
            capabilities=["knowledge tracing", "personalized recommendation", "weakness detection"],
            semantic_deps=["external_storage", "requires_cloud", "paid_api"],
            data=["student learning history"],
            resources=["Cloud Database", "GPT-4 API"]
        ),
        "player_b_architecture": build_arch_node(
            processing=["Local SQLite Ingestion", "Heuristic Rules Engine", "Local Dashboard UI"],
            capabilities=["knowledge tracing", "weakness detection", "personalized recommendation"],
            semantic_deps=[],
            data=["local student learning history"],
            resources=["Basic laptop", "Local Storage"],
            historical_decisions=[
                {
                    "historical_decision": "Use Local Heuristic Rules Engine",
                    "historical_evidence": {
                        "source_project": "EdTech Offline Mode 2023",
                        "evidence_pattern": "Rule-based analysis locally instead of cloud-based LLM inference.",
                        "why_it_worked": "Ensured 100% data privacy compliance while still offering actionable insights.",
                        "applicability": "Required when strict local data residency constraints apply."
                    },
                    "decision_status": "adopt",
                    "reasoning": "Data must strictly remain local per constraints, making cloud analysis infeasible."
                }
            ]
        ),
        "uncertainties": []
    }

    test_d = {
        "what": "Provide AI-powered real-time video analysis.",
        "why": "Detect objects immediately.",
        "how": "Cloud computer vision.",
        "constraints": ["offline", "no_gpu", "no_cloud", "no cameras", "24-hour prototype"],
        "requirements": [{"name": "detect objects immediately via video analysis", "required": True}],
        "gemini_baseline_architecture": build_arch_node(
            processing=["Camera Ingestion", "AWS Rekognition", "Realtime Dashboard"],
            capabilities=["object detection", "computer vision"],
            semantic_deps=["requires_camera", "requires_cloud", "requires_gpu", "external_storage"],
            data=["live video stream"],
            resources=["Camera", "Cloud Infrastructure", "GPU"]
        ),
        "player_b_architecture": build_arch_node(
            processing=["Edge Device Parsing", "Cloud-based YOLOv4", "Local Report"],
            capabilities=["object detection", "computer vision"],
            semantic_deps=["requires_camera", "requires_cloud"],
            data=["live video stream"],
            resources=["Camera", "5G connection"],
            historical_decisions=[
                {
                    "historical_decision": "Cloud-based YOLOv4",
                    "historical_evidence": {
                        "source_project": "City Traffic Analysis 2020",
                        "evidence_pattern": "Offload heavy video processing to the cloud.",
                        "why_it_worked": "Enabled high frame-rate processing without expensive edge hardware.",
                        "applicability": "Useful when local compute is constrained."
                    },
                    "decision_status": "adopt",
                    "reasoning": "Agent blindly proposes adopting this because the user has no local GPU, but fails to account for offline constraint."
                }
            ]
        ),
        "uncertainties": [
            {
                "id": "unc-camera",
                "question_text": "Can video acquisition exist without cameras?",
                "question_target": "Modality",
                "unknown_fact": "Is the user fundamentally relying on cameras?",
                "importance": "High",
                "yes_mutation": {"add_constraints": ["alternate_input_modality_allowed"], "remove_constraints": []},
                "no_mutation": {"add_constraints": ["camera_required"], "remove_constraints": []},
                "yes_candidate_architecture": build_arch_node(
                    processing=["Radar Sensor Data", "Edge ML Processing", "Dashboard"],
                    capabilities=["object detection"],
                    semantic_deps=["requires_gpu"],
                    data=["radar signatures"],
                    resources=["Radar modules", "Local Edge GPU"]
                ),
                "no_candidate_architecture": build_arch_node(
                    processing=["Local Video File Parsing", "CPU-based YOLOv4-tiny", "Local Report"],
                    capabilities=["object detection", "computer vision"],
                    semantic_deps=[],
                    data=["prerecorded video file"],
                    resources=["CPU"]
                )
            }
        ]
    }

    run_test("Test A: College Attendance", test_a)
    run_test("Test B: Waste Collection", test_b)
    run_test("Test C: Student Learning", test_c)
    run_test("Test D: The Impossible Case", test_d, answer_sequence=[
        {
            "answer": "YES",
            "new_player_b_architecture": build_arch_node(
                    processing=["Radar Sensor Data", "Edge ML Processing", "Dashboard"],
                    capabilities=["object detection"],
                    semantic_deps=["requires_gpu"],
                    data=["radar signatures"],
                    resources=["Radar modules", "Local Edge GPU"]
                ),
            "new_uncertainties": []
        },
        {
            "answer": "NO",
            "new_player_b_architecture": build_arch_node(
                    processing=["Local Video File Parsing", "CPU-based YOLOv4-tiny", "Local Report"],
                    capabilities=["object detection", "computer vision"],
                    semantic_deps=[],
                    data=["prerecorded video file"],
                    resources=["CPU"]
                ),
            "new_uncertainties": []
        }
    ])

if __name__ == "__main__":
    run_all()
