# Decision Engine Validation Tests

## Test A: College Attendance

**WHAT:** Automatically mark classroom attendance.
**WHY:** Manual attendance takes too much class time.
**CONSTRAINTS:** 50 students, 45-minute class, no paid APIs, Android phones, unreliable internet

### Raw Agent Payload
```json
{
  "what": "Automatically mark classroom attendance.",
  "why": "Manual attendance takes too much class time.",
  "how": "Students scan a QR code and the system verifies their presence.",
  "constraints": [
    "50 students",
    "45-minute class",
    "no paid APIs",
    "Android phones",
    "unreliable internet"
  ],
  "requirements": [
    {
      "name": "Mark classroom attendance",
      "required": true
    }
  ],
  "gemini_baseline_architecture": {
    "inputs": [
      "Data input"
    ],
    "processing": [
      "Cloud API Image Recognition",
      "Cloud Database Sync"
    ],
    "decision": [
      "Logic decision"
    ],
    "output": [
      "System Output"
    ],
    "capabilities": [
      "facial recognition attendance",
      "cloud storage"
    ],
    "data_required": [
      "high resolution images"
    ],
    "resources_required": [
      "Paid API",
      "Commercial Cloud Service"
    ],
    "constraints": []
  },
  "player_b_architecture": {
    "inputs": [
      "Data input"
    ],
    "processing": [
      "Local QR Code Generation",
      "Bluetooth/Wi-Fi Direct Sync",
      "Periodic Cloud Upload"
    ],
    "decision": [
      "Logic decision"
    ],
    "output": [
      "System Output"
    ],
    "capabilities": [
      "qr code attendance",
      "offline sync",
      "presence detection"
    ],
    "data_required": [
      "local student IDs"
    ],
    "resources_required": [
      "Local Server",
      "Android devices"
    ],
    "constraints": []
  },
  "uncertainties": [
    {
      "id": "unc-local-server",
      "question_text": "Is a local server permanently available in the classroom?",
      "question_target": "Local Server",
      "unknown_fact": "Local server availability",
      "importance": "High",
      "yes_mutation": {
        "add_constraints": [
          "local server available"
        ],
        "remove_constraints": []
      },
      "no_mutation": {
        "add_constraints": [
          "no local server"
        ],
        "remove_constraints": []
      },
      "yes_candidate_architecture": {
        "inputs": [
          "Data input"
        ],
        "processing": [
          "Local Server Auth",
          "Wi-Fi Direct Sync"
        ],
        "decision": [
          "Logic decision"
        ],
        "output": [
          "System Output"
        ],
        "capabilities": [
          "qr code attendance",
          "offline sync",
          "presence detection"
        ],
        "data_required": [
          "local student IDs"
        ],
        "resources_required": [
          "Local Server",
          "Android devices"
        ],
        "constraints": []
      },
      "no_candidate_architecture": {
        "inputs": [
          "Data input"
        ],
        "processing": [
          "Teacher Phone Master Auth",
          "Bluetooth Mesh Sync"
        ],
        "decision": [
          "Logic decision"
        ],
        "output": [
          "System Output"
        ],
        "capabilities": [
          "qr code attendance",
          "offline sync",
          "presence detection"
        ],
        "data_required": [
          "local student IDs"
        ],
        "resources_required": [
          "Teacher Android device",
          "Student Android devices"
        ],
        "constraints": []
      }
    }
  ]
}
```

### Battle Results (Gemini Baseline vs Evidence-Guided Candidate)

#### Gemini Baseline (Player A)
- **Architecture Name:** `Cloud API Image Recognition -> Cloud Database Sync`
- **Capabilities:** facial recognition attendance, cloud storage
- **Data Required:** high resolution images
- **Resources Required:** Paid API, Commercial Cloud Service
- **Requirements Met:** Mark classroom attendance
- **Constraint Violations:**
  - Requires 'Paid API' which violates constraint 'no paid APIs'.
  - Requires 'Commercial Cloud Service' which violates constraint 'no paid APIs'.
  - Cloud dependent without edge fallback violates constraint 'unreliable internet'.
- **Feasible?** False

#### Evidence-Guided Candidate (Player B)
- **Architecture Name:** `Local QR Code Generation -> Bluetooth/Wi-Fi Direct Sync -> Periodic Cloud Upload`
- **Capabilities:** qr code attendance, offline sync, presence detection
- **Data Required:** local student IDs
- **Resources Required:** Local Server, Android devices
- **Requirements Met:** Mark classroom attendance
- **Constraint Violations:**
  - None
- **Feasible?** True

**WINNER:** player_b (User architecture is infeasible. Player B wins.)

### Branch Candidate Impact Analysis

**Selected Uncertainty:** Is a local server permanently available in the classroom?
**Impact Score:** 1

---

## Test B: Waste Collection

**WHAT:** Reduce unnecessary garbage-collection trips.
**WHY:** Trucks visit bins that aren't full.
**CONSTRAINTS:** limited battery, poor connectivity, 48-hour prototype

### Raw Agent Payload
```json
{
  "what": "Reduce unnecessary garbage-collection trips.",
  "why": "Trucks visit bins that aren't full.",
  "how": "Use sensors to tell the truck when a bin needs collection.",
  "constraints": [
    "limited battery",
    "poor connectivity",
    "48-hour prototype"
  ],
  "requirements": [
    {
      "name": "Optimize waste collection",
      "required": true
    }
  ],
  "gemini_baseline_architecture": {
    "inputs": [
      "Data input"
    ],
    "processing": [
      "Continuous Video Stream",
      "Cloud ML Fill Detection",
      "Real-time Routing"
    ],
    "decision": [
      "Logic decision"
    ],
    "output": [
      "System Output"
    ],
    "capabilities": [
      "real-time waste monitoring",
      "dynamic routing"
    ],
    "data_required": [
      "continuous streaming video",
      "GPS data"
    ],
    "resources_required": [
      "Video cameras",
      "Cloud Servers",
      "High bandwidth 5G"
    ],
    "constraints": []
  },
  "player_b_architecture": {
    "inputs": [
      "Data input"
    ],
    "processing": [
      "Ultrasonic Fill Sensor",
      "Edge Threshold Trigger",
      "LoRaWAN periodic update",
      "Daily Route Gen"
    ],
    "decision": [
      "Logic decision"
    ],
    "output": [
      "System Output"
    ],
    "capabilities": [
      "fill level sensor monitoring",
      "dynamic routing"
    ],
    "data_required": [
      "low bandwidth sensor pings"
    ],
    "resources_required": [
      "Arduino/Ultrasonic sensors",
      "LoRaWAN Gateway",
      "Basic laptop"
    ],
    "constraints": []
  },
  "uncertainties": []
}
```

### Battle Results (Gemini Baseline vs Evidence-Guided Candidate)

#### Gemini Baseline (Player A)
- **Architecture Name:** `Continuous Video Stream -> Cloud ML Fill Detection -> Real-time Routing`
- **Capabilities:** real-time waste monitoring, dynamic routing
- **Data Required:** continuous streaming video, GPS data
- **Resources Required:** Video cameras, Cloud Servers, High bandwidth 5G
- **Requirements Met:** Optimize waste collection
- **Constraint Violations:**
  - Requires 'continuous streaming video' which violates constraint 'limited battery'.
  - Cloud dependent without edge fallback violates constraint 'poor connectivity'.
- **Feasible?** False

#### Evidence-Guided Candidate (Player B)
- **Architecture Name:** `Ultrasonic Fill Sensor -> Edge Threshold Trigger -> LoRaWAN periodic update -> Daily Route Gen`
- **Capabilities:** fill level sensor monitoring, dynamic routing
- **Data Required:** low bandwidth sensor pings
- **Resources Required:** Arduino/Ultrasonic sensors, LoRaWAN Gateway, Basic laptop
- **Requirements Met:** Optimize waste collection
- **Constraint Violations:**
  - None
- **Feasible?** True

**WINNER:** player_b (User architecture is infeasible. Player B wins.)

### Conclusion
Journey finished. No uncertainties to explore.
## Test C: Student Learning

**WHAT:** Help students identify topics they are weak in.
**WHY:** Students don't know what to practice.
**CONSTRAINTS:** no external storage, student data must stay locally, basic laptop, 48-hour prototype

### Raw Agent Payload
```json
{
  "what": "Help students identify topics they are weak in.",
  "why": "Students don't know what to practice.",
  "how": "Analyze their previous practice and recommend questions.",
  "constraints": [
    "no external storage",
    "student data must stay locally",
    "basic laptop",
    "48-hour prototype"
  ],
  "requirements": [
    {
      "name": "Help identify topics they are weak in",
      "required": true
    }
  ],
  "gemini_baseline_architecture": {
    "inputs": [
      "Data input"
    ],
    "processing": [
      "Upload student history",
      "OpenAI GPT-4 Analysis",
      "Generate Recommendations"
    ],
    "decision": [
      "Logic decision"
    ],
    "output": [
      "System Output"
    ],
    "capabilities": [
      "knowledge tracing",
      "personalized recommendation",
      "weakness detection"
    ],
    "data_required": [
      "student learning history"
    ],
    "resources_required": [
      "Cloud Database",
      "GPT-4 API"
    ],
    "constraints": []
  },
  "player_b_architecture": {
    "inputs": [
      "Data input"
    ],
    "processing": [
      "Local SQLite Ingestion",
      "Heuristic Rules Engine",
      "Local Dashboard UI"
    ],
    "decision": [
      "Logic decision"
    ],
    "output": [
      "System Output"
    ],
    "capabilities": [
      "knowledge tracing",
      "weakness detection",
      "personalized recommendation"
    ],
    "data_required": [
      "local student learning history"
    ],
    "resources_required": [
      "Basic laptop",
      "Local Storage"
    ],
    "constraints": []
  },
  "uncertainties": []
}
```

### Battle Results (Gemini Baseline vs Evidence-Guided Candidate)

#### Gemini Baseline (Player A)
- **Architecture Name:** `Upload student history -> OpenAI GPT-4 Analysis -> Generate Recommendations`
- **Capabilities:** knowledge tracing, personalized recommendation, weakness detection
- **Data Required:** student learning history
- **Resources Required:** Cloud Database, GPT-4 API
- **Requirements Met:** Help identify topics they are weak in
- **Constraint Violations:**
  - None
- **Feasible?** True

#### Evidence-Guided Candidate (Player B)
- **Architecture Name:** `Local SQLite Ingestion -> Heuristic Rules Engine -> Local Dashboard UI`
- **Capabilities:** knowledge tracing, weakness detection, personalized recommendation
- **Data Required:** local student learning history
- **Resources Required:** Basic laptop, Local Storage
- **Requirements Met:** Help identify topics they are weak in
- **Constraint Violations:**
  - None
- **Feasible?** True

**WINNER:** tie (Both are feasible and satisfy requirements equally. Neither has a decisive advantage under current constraints.)

### Conclusion
Journey finished. No uncertainties to explore.
## Test D: The Impossible Case

**WHAT:** Provide AI-powered real-time video analysis.
**WHY:** Detect objects immediately.
**CONSTRAINTS:** offline, no_gpu, no_cloud, no cameras, 24-hour prototype

### Raw Agent Payload
```json
{
  "what": "Provide AI-powered real-time video analysis.",
  "why": "Detect objects immediately.",
  "how": "Cloud computer vision.",
  "constraints": [
    "offline",
    "no_gpu",
    "no_cloud",
    "no cameras",
    "24-hour prototype"
  ],
  "requirements": [
    {
      "name": "detect objects immediately via video analysis",
      "required": true
    }
  ],
  "gemini_baseline_architecture": {
    "inputs": [
      "Data input"
    ],
    "processing": [
      "Camera Ingestion",
      "AWS Rekognition",
      "Realtime Dashboard"
    ],
    "decision": [
      "Logic decision"
    ],
    "output": [
      "System Output"
    ],
    "capabilities": [
      "object detection",
      "computer vision"
    ],
    "data_required": [
      "live video stream"
    ],
    "resources_required": [
      "Camera",
      "Cloud Infrastructure",
      "GPU"
    ],
    "constraints": []
  },
  "player_b_architecture": {
    "inputs": [
      "Data input"
    ],
    "processing": [
      "Edge Device Parsing",
      "Cloud-based YOLOv4",
      "Local Report"
    ],
    "decision": [
      "Logic decision"
    ],
    "output": [
      "System Output"
    ],
    "capabilities": [
      "object detection",
      "computer vision"
    ],
    "data_required": [
      "live video stream"
    ],
    "resources_required": [
      "Camera",
      "5G connection"
    ],
    "constraints": []
  },
  "uncertainties": []
}
```

### Battle Results (Gemini Baseline vs Evidence-Guided Candidate)

#### Gemini Baseline (Player A)
- **Architecture Name:** `Camera Ingestion -> AWS Rekognition -> Realtime Dashboard`
- **Capabilities:** object detection, computer vision
- **Data Required:** live video stream
- **Resources Required:** Camera, Cloud Infrastructure, GPU
- **Requirements Met:** detect objects immediately via video analysis
- **Constraint Violations:**
  - Requires 'Cloud Infrastructure' which violates constraint 'offline'.
  - Requires 'GPU' which violates constraint 'no_gpu'.
  - Requires 'Cloud Infrastructure' which violates constraint 'no_cloud'.
  - Requires 'Camera' which violates constraint 'no cameras'.
- **Feasible?** False

#### Evidence-Guided Candidate (Player B)
- **Architecture Name:** `Edge Device Parsing -> Cloud-based YOLOv4 -> Local Report`
- **Capabilities:** object detection, computer vision
- **Data Required:** live video stream
- **Resources Required:** Camera, 5G connection
- **Requirements Met:** detect objects immediately via video analysis
- **Constraint Violations:**
  - Requires 'Camera' which violates constraint 'no cameras'.
- **Feasible?** False

**WINNER:** tie (Both architectures are infeasible.)

### Conclusion
Journey finished. No uncertainties to explore.
**NO_FEASIBLE_CANDIDATE_ARCHITECTURE_FOUND**

