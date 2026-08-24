import json
from pathlib import Path

patterns_dir = Path(__file__).parent / "patterns"
patterns_dir.mkdir(exist_ok=True)

patterns = [
    {
        "pattern_id": "pattern_smartphone_substitution_01",
        "domain": "Cross-Domain",
        "pattern": "Winning solutions frequently democratize access by replacing expensive, specialized hardware with ubiquitous smartphone sensors (camera, IMU) paired with edge ML.",
        "observed_in_projects": ["sih_2023_ag_01", "sih_2024_hc_02", "sih_2024_trans_02"],
        "evidence": [
            "sih_2023_ag_01: Uses smartphone camera instead of specialized agronomy tests for crop disease.",
            "sih_2024_hc_02: Uses flash photo of eyelid to estimate hemoglobin, replacing invasive blood tests.",
            "sih_2024_trans_02: Uses phone IMU instead of specialized road surface profiling vehicles."
        ],
        "confidence": "high"
    },
    {
        "pattern_id": "pattern_offline_accessibility_01",
        "domain": "Agriculture & FinTech",
        "pattern": "Solutions targeting rural populations succeed when they explicitly remove dependencies on high-speed internet or smartphones.",
        "observed_in_projects": ["sih_2023_fin_01", "sih_2023_ag_01"],
        "evidence": [
            "sih_2023_fin_01: IVR-based voice UPI works on feature phones without data.",
            "sih_2023_ag_01: CNN model runs entirely on-device (TFLite) without needing cloud inference."
        ],
        "confidence": "high"
    },
    {
        "pattern_id": "pattern_proactive_routing_01",
        "domain": "Healthcare & Disaster Management",
        "pattern": "Effective resource management projects shift the workflow from reactive assignment to proactive, predictive routing and load balancing.",
        "observed_in_projects": ["sih_2022_hc_01", "sih_2020_dis_01", "sih_2022_tr_01"],
        "evidence": [
            "sih_2022_hc_01: Predicts bed shortages and routes patients before bottlenecks occur.",
            "sih_2020_dis_01: Pre-emptively routes rescue boats based on aggregated predictive map.",
            "sih_2022_tr_01: Traffic lights are scheduled dynamically ahead of congestion."
        ],
        "confidence": "medium"
    },
    {
        "pattern_id": "pattern_decentralized_trust_01",
        "domain": "Governance",
        "pattern": "When the core problem is systemic fraud or forgery, blockchain and cryptographic hashing are standard winning approaches for verification.",
        "observed_in_projects": ["sih_2023_gov_01"],
        "evidence": [
            "sih_2023_gov_01: Solves certificate forgery entirely via decentralized hashing rather than centralized DBs."
        ],
        "confidence": "low"
    }
]

for p in patterns:
    file_path = patterns_dir / f"{p['pattern_id']}.json"
    with open(file_path, "w") as f:
        json.dump(p, f, indent=2)

print(f"Generated {len(patterns)} patterns.")
