import csv
import json
import requests
from pathlib import Path

original_csv = Path("benchmark_suite/level6/results/v1_initial_report.csv")
corrected_csv = Path("benchmark_suite/level6/results/v1.1_corrected_report.csv")

scenarios_dir = Path("benchmark_suite/scenarios")

with open(original_csv, "r") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

new_rows = []
for row in rows:
    name = row["Scenario"]
    
    with open(scenarios_dir / f"{name}.json", "r") as f:
        scenario = json.load(f)
        
    try:
        state = requests.get(f"http://127.0.0.1:8000/api/journey/{name}-session/state").json()
    except Exception as e:
        print(f"Error fetching state for {name}: {e}")
        new_rows.append(row)
        continue
        
    try:
        terminals = [n for n in state["decision_graph"] if n["status"] == "TERMINAL"]
    except KeyError:
        print(f"KeyError for {name}. State was: {state}")
        new_rows.append(row)
        continue
    
    bp_f = False
    oracle_hit = False
    
    feasible_terminals = [t for t in terminals if t.get("architecture", {}).get("candidate_status") == "FEASIBLE"]
    
    if feasible_terminals:
        best_t = max(feasible_terminals, key=lambda x: x.get("path_score", 0.0) or 0.0)
        bp_f = True
        
        if "oracle_architecture" in scenario:
            o_decisions = scenario["oracle_architecture"].get("architectural_decisions", {})
            t_decisions = best_t["architecture"].get("architectural_decisions", {})
            if list(o_decisions.values()) == list(t_decisions.values()):
                oracle_hit = True

    base_real_f = row["Baseline_Real_F"] == "True"
    delta_f = 1 if (bp_f and not base_real_f) else 0

    row["BP_F"] = str(bp_f)
    row["Delta_F"] = str(delta_f)
    row["Oracle_Hit"] = str(oracle_hit)
    new_rows.append(row)

with open(corrected_csv, "w", newline="") as f:
    if len(new_rows) > 0:
        writer = csv.DictWriter(f, fieldnames=new_rows[0].keys())
        writer.writeheader()
        writer.writerows(new_rows)
        
print("Recalculation complete. Results written to v1.1_corrected_report.csv")
