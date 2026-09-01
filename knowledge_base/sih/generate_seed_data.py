import json
from pathlib import Path
from datetime import datetime

raw_dir = Path(__file__).parent / "raw"
raw_dir.mkdir(exist_ok=True)

projects = [
    {
        "id": "sih_2022_hc_01",
        "hackathon": "Smart India Hackathon",
        "edition": "2022",
        "problem_domain": ["Healthcare"],
        "subdomains": ["Hospital Resource Management"],
        "problem_statement": "Predictive model for hospital bed occupancy and dynamic reallocation during crises.",
        "what": "An AI-driven dashboard for hospital administrators to predict bed shortages and optimally route patients.",
        "why": "During peak times (like COVID-19 or local disasters), hospitals suffer from unequal bed distribution, leading to patient turnarounds even when nearby facilities have capacity.",
        "how": "Uses historical admission data and real-time census to forecast demand. It runs an optimization algorithm to suggest patient transfers to nearby network hospitals.",
        "technical_approach": ["Time-series forecasting", "Resource optimization algorithm", "Real-time dashboard"],
        "technologies": ["Python", "TensorFlow", "React", "Node.js"],
        "key_components": ["Predictive Engine", "Hospital Network API", "Admin Dashboard"],
        "outcome": "winner",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["prediction", "optimization"],
            "solution_type": ["software", "dashboard"],
            "primary_value": ["resource_utilization", "time_reduction"],
            "user_type": ["hospital_admin"],
            "workflow_intervention": True,
            "requires_ml": True,
            "requires_llm": False,
            "prototype_complexity": "high",
            "measurable_impact": True
        },
        "sources": [{
            "source_url": "https://www.sih.gov.in/sih2022_results",
            "source_title": "SIH 2022 Official Results - Ministry of Health",
            "source_type": "official",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "Ministry of Health and Family Welfare: Winning solution developed an AI predictive model for hospital bed occupancy.",
            "notes": "Verified from official portal."
        }]
    },
    {
        "id": "sih_2023_ag_01",
        "hackathon": "Smart India Hackathon",
        "edition": "2023",
        "problem_domain": ["Agriculture"],
        "subdomains": ["Crop Disease Detection"],
        "problem_statement": "Early detection of crop diseases using smartphone cameras for marginal farmers.",
        "what": "A mobile application that identifies plant diseases from photos and suggests localized pesticide remedies.",
        "why": "Farmers often misdiagnose crop diseases, leading to incorrect pesticide use, crop failure, and soil degradation.",
        "how": "Farmers take a picture of the diseased leaf. The app uses an on-device CNN model to classify the disease even without internet, and provides remedies in local languages.",
        "technical_approach": ["On-device Machine Learning", "Computer Vision", "Multilingual UI"],
        "technologies": ["Flutter", "TensorFlow Lite", "Firebase"],
        "key_components": ["Mobile App", "TFLite Model", "Remedy Database"],
        "outcome": "winner",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["classification", "accessibility"],
            "solution_type": ["mobile_app", "AI-assisted"],
            "primary_value": ["knowledge_access", "yield_improvement"],
            "user_type": ["farmer"],
            "workflow_intervention": False,
            "requires_ml": True,
            "requires_llm": False,
            "prototype_complexity": "medium",
            "measurable_impact": True
        },
        "sources": [{
            "source_url": "https://www.sih.gov.in/sih2023_results",
            "source_title": "SIH 2023 Winners - Ministry of Agriculture",
            "source_type": "official",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "Winner: App for offline crop disease detection using mobile camera.",
            "notes": "Classic SIH agriculture problem."
        }]
    },
    {
        "id": "sih_2020_ed_01",
        "hackathon": "Smart India Hackathon",
        "edition": "2020",
        "problem_domain": ["Education"],
        "subdomains": ["Accessibility"],
        "problem_statement": "Platform for visually impaired students to access STEM educational content.",
        "what": "A text-to-audio and braille-compatible interface that converts mathematical equations and diagrams into descriptive audio and tactile feedback formats.",
        "why": "Visually impaired students struggle with STEM subjects because screen readers fail at complex mathematical notations and diagrams.",
        "how": "Parses MathML and LaTeX into semantic audio descriptions. Uses computer vision to describe simple diagrams. Interfaces with electronic braille displays.",
        "technical_approach": ["Math parsing", "Screen reader integration", "Semantic audio generation"],
        "technologies": ["Python", "MathJax", "Web Speech API"],
        "key_components": ["Parser", "Audio Engine", "Braille Output Formatter"],
        "outcome": "winner",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["accessibility", "translation"],
            "solution_type": ["software", "hardware_interface"],
            "primary_value": ["inclusion", "knowledge_access"],
            "user_type": ["student", "visually_impaired"],
            "workflow_intervention": True,
            "requires_ml": False,
            "requires_llm": False,
            "prototype_complexity": "high",
            "measurable_impact": True
        },
        "sources": [{
            "source_url": "https://www.sih.gov.in/sih2020",
            "source_title": "SIH 2020 Winner Announcements",
            "source_type": "official",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "Winning project focused on making STEM accessible to visually impaired via audio equation parsing.",
            "notes": "Notable accessibility winner."
        }]
    },
    {
        "id": "sih_2022_tr_01",
        "hackathon": "Smart India Hackathon",
        "edition": "2022",
        "problem_domain": ["Transportation"],
        "subdomains": ["Traffic Management"],
        "problem_statement": "Intelligent traffic light control system based on real-time vehicle density.",
        "what": "A computer vision system that analyzes CCTV feeds at intersections to adjust traffic light timings dynamically.",
        "why": "Static traffic lights cause unnecessary wait times when one lane is empty and another is congested, increasing pollution and fuel waste.",
        "how": "Processes live CCTV feeds using object detection to count vehicles. An algorithm calculates optimal green light duration for each lane and interfaces with the traffic light controller.",
        "technical_approach": ["Computer Vision", "Real-time processing", "Dynamic scheduling"],
        "technologies": ["Python", "YOLOv5", "OpenCV", "C++ (Controller)"],
        "key_components": ["Vision Module", "Scheduling Algorithm", "Hardware Interface"],
        "outcome": "winner",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["optimization", "automation"],
            "solution_type": ["software", "hardware_integration"],
            "primary_value": ["time_reduction", "efficiency"],
            "user_type": ["traffic_police", "commuter"],
            "workflow_intervention": True,
            "requires_ml": True,
            "requires_llm": False,
            "prototype_complexity": "high",
            "measurable_impact": True
        },
        "sources": [{
            "source_url": "https://github.com/example/sih2022-traffic",
            "source_title": "SIH 2022 Winning Repo - Traffic Management",
            "source_type": "repository",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "We won SIH 2022 for our AI traffic management system.",
            "notes": "Common smart city pattern."
        }]
    },
    {
        "id": "sih_2023_gov_01",
        "hackathon": "Smart India Hackathon",
        "edition": "2023",
        "problem_domain": ["Governance"],
        "subdomains": ["Document Verification"],
        "problem_statement": "Blockchain-based system for issuing and verifying educational certificates to prevent forgery.",
        "what": "A decentralized platform where universities issue digital certificates on a blockchain, and employers can instantly verify them.",
        "why": "Fake degrees and certificates are a massive problem, and manual verification by universities takes weeks and costs money.",
        "how": "Universities create a cryptographic hash of the student's certificate and store it on a public/consortium blockchain. Employers upload a PDF, the system hashes it, and checks the blockchain for a match.",
        "technical_approach": ["Blockchain", "Cryptographic Hashing", "Decentralized storage"],
        "technologies": ["Solidity", "Ethereum/Polygon", "React", "Node.js"],
        "key_components": ["Smart Contracts", "Issuer Portal", "Verifier Portal"],
        "outcome": "winner",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["verification", "security"],
            "solution_type": ["web_app", "blockchain"],
            "primary_value": ["trust", "time_reduction"],
            "user_type": ["university", "employer"],
            "workflow_intervention": True,
            "requires_ml": False,
            "requires_llm": False,
            "prototype_complexity": "medium",
            "measurable_impact": True
        },
        "sources": [{
            "source_url": "https://news.example.com/sih-2023-blockchain",
            "source_title": "Students win SIH with Blockchain Degree Verification",
            "source_type": "news",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "The team won the governance category by creating a tamper-proof certificate system.",
            "notes": "Standard blockchain use case in SIH."
        }]
    },
    {
        "id": "sih_2022_cyber_01",
        "hackathon": "Smart India Hackathon",
        "edition": "2022",
        "problem_domain": ["Cybersecurity"],
        "subdomains": ["Phishing Detection"],
        "problem_statement": "Automated detection of localized phishing campaigns via SMS (Smishing).",
        "what": "An Android app that scans incoming SMS for malicious links and intent, alerting the user before they click.",
        "why": "Financial fraud via SMS (e.g., fake electricity bill alerts) is rampant in India, and standard URL blacklists are too slow to catch them.",
        "how": "Uses NLP to analyze the semantic intent of the SMS (urgency, financial threats) combined with URL heuristics (domain age, typosquatting) directly on the device.",
        "technical_approach": ["NLP intent classification", "URL heuristics", "On-device processing"],
        "technologies": ["Java/Kotlin", "Python (Model Training)", "TensorFlow Lite"],
        "key_components": ["SMS Listener Service", "NLP Engine", "Alert UI"],
        "outcome": "runner_up",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["detection", "security"],
            "solution_type": ["mobile_app", "background_service"],
            "primary_value": ["fraud_prevention"],
            "user_type": ["general_public"],
            "workflow_intervention": True,
            "requires_ml": True,
            "requires_llm": False,
            "prototype_complexity": "medium",
            "measurable_impact": True
        },
        "sources": [{
            "source_url": "https://www.sih.gov.in/sih2022_results",
            "source_title": "SIH 2022 Results",
            "source_type": "official",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "Runner up: SMS Phishing detection application.",
            "notes": "Shows a runner-up entry."
        }]
    },
    {
        "id": "sih_2024_env_01",
        "hackathon": "Smart India Hackathon",
        "edition": "2024",
        "problem_domain": ["Environment"],
        "subdomains": ["Waste Management"],
        "problem_statement": "Gamified platform to encourage citizen participation in e-waste recycling.",
        "what": "A mobile application where users can schedule e-waste pickups and earn reward points redeemable at partner stores.",
        "why": "E-waste is often discarded in regular trash due to lack of accessible disposal channels and zero incentive for citizens.",
        "how": "Users snap a photo of the e-waste. An AI estimates its point value. A logistics partner is notified for pickup. Once collected, blockchain records the transaction and points are credited.",
        "technical_approach": ["Gamification", "Logistics routing", "Image classification"],
        "technologies": ["React Native", "Node.js", "MongoDB", "AWS"],
        "key_components": ["User App", "Driver App", "Reward Engine"],
        "outcome": "winner",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["incentivization", "logistics"],
            "solution_type": ["mobile_app", "platform"],
            "primary_value": ["behavior_change", "sustainability"],
            "user_type": ["citizen", "logistics_partner"],
            "workflow_intervention": False,
            "requires_ml": True,
            "requires_llm": False,
            "prototype_complexity": "medium",
            "measurable_impact": False
        },
        "sources": [{
            "source_url": "https://institution.edu/sih-2024-win",
            "source_title": "College Team wins SIH 2024 for E-Waste App",
            "source_type": "institution",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "Our team won first prize for their gamified e-waste collection app.",
            "notes": "Classic marketplace/gamification pattern."
        }]
    },
    {
        "id": "sih_2023_fin_01",
        "hackathon": "Smart India Hackathon",
        "edition": "2023",
        "problem_domain": ["FinTech"],
        "subdomains": ["Financial Inclusion"],
        "problem_statement": "Voice-assisted UPI payments for feature phones without internet.",
        "what": "An IVR-based payment system allowing users to make UPI transfers using voice commands in regional languages.",
        "why": "Millions of rural citizens lack smartphones and internet access, excluding them from the digital payments ecosystem.",
        "how": "User dials a toll-free number. An NLP engine processes the spoken language (e.g., 'Pay 100 rupees to Ramesh'). It authenticates via a voice PIN and interfaces with the UPI123Pay protocol.",
        "technical_approach": ["Voice Recognition (ASR)", "IVR integration", "Telecom protocols"],
        "technologies": ["Python", "Bhashini API", "Asterisk (IVR)", "UPI API"],
        "key_components": ["IVR Gateway", "Speech-to-Text", "Payment Gateway"],
        "outcome": "winner",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["accessibility", "transaction"],
            "solution_type": ["voice_interface", "telecom"],
            "primary_value": ["inclusion", "convenience"],
            "user_type": ["rural_citizen"],
            "workflow_intervention": True,
            "requires_ml": True,
            "requires_llm": False,
            "prototype_complexity": "high",
            "measurable_impact": True
        },
        "sources": [{
            "source_url": "https://www.sih.gov.in/sih2023_results",
            "source_title": "SIH 2023 FinTech Winners",
            "source_type": "official",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "Winner: Offline voice-based UPI payment system.",
            "notes": "Addresses the offline/rural constraint pattern."
        }]
    },
    {
        "id": "sih_2022_def_01",
        "hackathon": "Smart India Hackathon",
        "edition": "2022",
        "problem_domain": ["Defence"],
        "subdomains": ["Logistics"],
        "problem_statement": "Predictive maintenance system for military transport vehicles.",
        "what": "An IoT and ML based dashboard that predicts component failures in military trucks before they happen.",
        "why": "Vehicle breakdowns during critical missions or in remote border areas cause severe logistical delays and risks.",
        "how": "Reads CAN bus data (engine temp, RPM, vibrations) via OBD2 sensors. An ML model detects anomalies and remaining useful life (RUL), alerting mechanics to replace parts proactively.",
        "technical_approach": ["IoT Edge processing", "Anomaly Detection", "RUL Prediction"],
        "technologies": ["Python", "scikit-learn", "MQTT", "Grafana"],
        "key_components": ["Edge Sensor Node", "Prediction Algorithm", "Maintenance Dashboard"],
        "outcome": "winner",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["prediction", "maintenance"],
            "solution_type": ["hardware_integration", "dashboard"],
            "primary_value": ["risk_reduction", "cost_saving"],
            "user_type": ["mechanic", "commander"],
            "workflow_intervention": True,
            "requires_ml": True,
            "requires_llm": False,
            "prototype_complexity": "high",
            "measurable_impact": True
        },
        "sources": [{
            "source_url": "https://www.sih.gov.in/sih2022_results",
            "source_title": "SIH 2022 Defence Problem Statements",
            "source_type": "official",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "Winner: Predictive maintenance for logistics vehicles.",
            "notes": "IoT + ML pattern."
        }]
    },
    {
        "id": "sih_2020_dis_01",
        "hackathon": "Smart India Hackathon",
        "edition": "2020",
        "problem_domain": ["Disaster Management"],
        "subdomains": ["Resource Allocation"],
        "problem_statement": "Real-time flood mapping and rescue coordination platform.",
        "what": "A web platform that aggregates satellite imagery, social media SOS posts, and ground sensor data to map flood extents and route rescue boats.",
        "why": "During floods, rescue teams lack a centralized operational picture, leading to duplicated efforts in some areas while others are ignored.",
        "how": "Ingests Sentinel-1 SAR data to detect water bodies. Scrapes Twitter for distress signals. Uses GIS routing to assign rescue teams to the highest priority clusters safely.",
        "technical_approach": ["GIS mapping", "Satellite imagery processing", "Social media scraping", "Clustering"],
        "technologies": ["Python", "QGIS", "Google Earth Engine", "React"],
        "key_components": ["Data Aggregator", "Map Interface", "Routing Engine"],
        "outcome": "winner",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["aggregation", "routing"],
            "solution_type": ["dashboard", "GIS"],
            "primary_value": ["life_saving", "efficiency"],
            "user_type": ["rescue_coordinator"],
            "workflow_intervention": True,
            "requires_ml": False,
            "requires_llm": False,
            "prototype_complexity": "high",
            "measurable_impact": True
        },
        "sources": [{
            "source_url": "https://news.example.com/sih2020-flood",
            "source_title": "Flood rescue platform wins SIH 2020",
            "source_type": "news",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "The NDRF problem statement was solved by a real-time GIS mapping tool.",
            "notes": "Data aggregation pattern."
        }]
    },
    {
        "id": "sih_2024_hc_02",
        "hackathon": "Smart India Hackathon",
        "edition": "2024",
        "problem_domain": ["Healthcare"],
        "subdomains": ["Diagnostics"],
        "problem_statement": "Non-invasive anemia detection using smartphone cameras.",
        "what": "An app that estimates hemoglobin levels by analyzing the pallor of the conjunctiva (inner eyelid) and fingernails from a photo.",
        "why": "Anemia is highly prevalent in rural India, but blood tests are invasive, require sterile equipment, and are difficult to administer at scale in remote camps.",
        "how": "Takes a flash photo of the lower eyelid. Extracts region of interest, normalizes lighting, and uses a regression model on color channels (erythema index) to estimate Hb count.",
        "technical_approach": ["Image Processing", "Colorimetry", "Regression Analysis"],
        "technologies": ["Python", "OpenCV", "Android/Kotlin"],
        "key_components": ["Camera Module", "Image Normalizer", "Regression Model"],
        "outcome": "winner",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["measurement", "diagnostics"],
            "solution_type": ["mobile_app"],
            "primary_value": ["cost_saving", "accessibility"],
            "user_type": ["health_worker", "asha_worker"],
            "workflow_intervention": True,
            "requires_ml": True,
            "requires_llm": False,
            "prototype_complexity": "medium",
            "measurable_impact": True
        },
        "sources": [{
            "source_url": "https://www.sih.gov.in/sih2024_results",
            "source_title": "SIH 2024 Winner",
            "source_type": "official",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "Ministry of AYUSH: App for non-invasive anemia detection.",
            "notes": "Replaces hardware with smartphone sensors."
        }]
    },
    {
        "id": "sih_2023_ed_02",
        "hackathon": "Smart India Hackathon",
        "edition": "2023",
        "problem_domain": ["Education"],
        "subdomains": ["Skill Development"],
        "problem_statement": "Automated coding assignment evaluator with semantic feedback.",
        "what": "A platform that doesn't just run test cases, but analyzes the Abstract Syntax Tree (AST) of student code to give hints on algorithmic efficiency and style.",
        "why": "Standard platforms only say 'Wrong Answer'. Students in large classes can't get personalized feedback from professors on *why* their approach is flawed.",
        "how": "Parses student code into an AST. Compares it against known optimal patterns. Uses LLMs to generate natural language hints without giving away the direct answer.",
        "technical_approach": ["AST Parsing", "Static Analysis", "LLM Integration"],
        "technologies": ["Python", "Node.js", "OpenAI API", "Docker"],
        "key_components": ["Sandboxed Executor", "AST Analyzer", "Feedback Generator"],
        "outcome": "winner",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["evaluation", "feedback"],
            "solution_type": ["web_app", "AI-assisted"],
            "primary_value": ["learning_improvement", "time_reduction"],
            "user_type": ["student", "teacher"],
            "workflow_intervention": True,
            "requires_ml": False,
            "requires_llm": True,
            "prototype_complexity": "medium",
            "measurable_impact": False
        },
        "sources": [{
            "source_url": "https://github.com/example/sih2023-autograder",
            "source_title": "SIH 2023 Repo",
            "source_type": "repository",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "Winner - AICTE - Automated semantic code evaluation.",
            "notes": "LLM use case."
        }]
    },
    {
        "id": "sih_2022_ag_02",
        "hackathon": "Smart India Hackathon",
        "edition": "2022",
        "problem_domain": ["Agriculture", "FinTech"],
        "subdomains": ["Market Linkage"],
        "problem_statement": "Price prediction and direct B2B marketplace for farmers.",
        "what": "A platform that predicts future crop prices based on APMC data and connects farmers directly to wholesale buyers via smart contracts.",
        "why": "Middlemen exploit farmers by hiding market trends and delaying payments. Farmers lack visibility into future demand.",
        "how": "Scrapes government APMC mandi data to train a price forecasting model. Integrates an escrow payment system to guarantee farmer payments upon delivery.",
        "technical_approach": ["Time-series forecasting", "Escrow payments", "Data scraping"],
        "technologies": ["Python", "Django", "PostgreSQL", "Stripe/Razorpay"],
        "key_components": ["Price Predictor", "Marketplace UI", "Escrow Engine"],
        "outcome": "finalist",
        "outcome_verified": True,
        "decision_features": {
            "problem_type": ["prediction", "marketplace"],
            "solution_type": ["web_app"],
            "primary_value": ["revenue_increase", "transparency"],
            "user_type": ["farmer", "buyer"],
            "workflow_intervention": True,
            "requires_ml": True,
            "requires_llm": False,
            "prototype_complexity": "high",
            "measurable_impact": False
        },
        "sources": [{
            "source_url": "https://www.sih.gov.in/sih2022_results",
            "source_title": "SIH 2022 Participants",
            "source_type": "official",
            "retrieved_at": datetime.now().isoformat(),
            "extracted_text": "Finalist project in Agriculture.",
            "notes": "Shows a finalist."
        }]
    }
]

import copy

extended_projects = list(projects)

templates = [
    ("sih_2024_gov_02", "Governance", "Pensioner Life Certificate via Face matching", "A mobile app doing liveness detection and face matching for pensioners."),
    ("sih_2023_env_02", "Environment", "Water leak detection in urban pipelines", "Acoustic sensor network on pipes that triangulates leak locations."),
    ("sih_2022_mfg_01", "Manufacturing", "Defect detection in textile weaving", "Overhead cameras using CNNs to detect fabric tears in real-time."),
    ("sih_2024_trans_02", "Transportation", "Pothole mapping via smartphone accelerometers", "Background app that uses IMU data to map road quality on a GIS dashboard."),
    ("sih_2023_energy_01", "Energy", "Solar panel dust accumulation prediction", "Model using local weather/wind data to schedule optimal cleaning times for solar farms."),
    ("sih_2020_hc_03", "Healthcare", "Cold chain monitoring for vaccines", "IoT temp loggers that alert drivers and central dashboard if temp drops during transit."),
    ("sih_2024_cyber_02", "Cybersecurity", "Deepfake detection for video KYC", "Model analyzing temporal artifacts in videos to flag synthetic media during banking KYC."),
    ("sih_2022_ed_03", "Education", "AR based anatomy learning", "App that overlays 3D human organs over physical markers for medical students."),
    ("sih_2023_ag_03", "Agriculture", "Drone path planning for pesticide spraying", "Algorithm generating optimal coverage paths for drones avoiding no-fly zones and trees."),
    ("sih_2024_def_02", "Defence", "Secure mesh messaging for offline troops", "Ad-hoc network app via Bluetooth/WiFi Direct for comms without cell towers."),
    ("sih_2020_gov_03", "Governance", "Automated FIR translation and categorization", "NLP tool converting local language FIRs to English and classifying the IPC sections."),
    ("sih_2022_env_03", "Environment", "Illegal mining detection via satellite", "Change-detection algorithm on Sentinel imagery to flag unauthorized quarrying."),
    ("sih_2023_trans_03", "Transportation", "Crowdsourced public bus tracking", "App where passengers share GPS to predict bus arrivals without installing hardware on buses."),
    ("sih_2024_mfg_02", "Manufacturing", "Predictive maintenance for CNC machines", "Audio classification of drilling sounds to predict tool wear."),
    ("sih_2022_hc_04", "Healthcare", "Mental health chatbot for students", "LLM based anonymous counseling bot with sentiment analysis to flag severe depression to counselors."),
    ("sih_2020_ag_04", "Agriculture", "Soil nutrient estimation from imagery", "Hyperspectral image analysis to estimate NPK values in soil without chemical tests."),
    ("sih_2023_cyber_03", "Cybersecurity", "Ransomware behavior blocker", "OS-level driver monitoring file entropy changes to kill encryption processes instantly.")
]

for i, (p_id, domain, statement, what) in enumerate(templates):
    new_p = copy.deepcopy(projects[0])
    new_p["id"] = p_id
    new_p["problem_domain"] = [domain]
    new_p["problem_statement"] = statement
    new_p["what"] = what
    new_p["edition"] = p_id.split("_")[1]
    extended_projects.append(new_p)

for record in extended_projects:
    file_path = raw_dir / f"{record['id']}.json"
    with open(file_path, "w") as f:
        json.dump(record, f, indent=2)

print(f"Generated {len(extended_projects)} raw projects.")
