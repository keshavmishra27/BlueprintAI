import os
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pipeline.ingest import ingest_raw_data
from pipeline.normalize import normalize_records
from pipeline.deduplicate import deduplicate_records
from pipeline.statistics import generate_statistics, print_statistics

def main():
    base_dir = Path(__file__).resolve().parent.parent
    raw_dir = base_dir / "raw"
    normalized_dir = base_dir / "normalized"
    
    print("--- Starting SIH Knowledge Base Pipeline ---")
    
    print(f"Ingesting raw data from {raw_dir}...")
    raw_records = ingest_raw_data(raw_dir)
    print(f"Ingested {len(raw_records)} raw records.")
    
    if not raw_records:
        print("No raw records found. Exiting.")
        return
        
    print("Normalizing and validating records...")
    validated, errors = normalize_records(raw_records)
    print(f"Successfully validated {len(validated)} records.")
    if errors:
        print(f"Failed to validate {len(errors)} records.")
        for err in errors:
            print(f"  - Record {err['record_id']}: {err['error']}")
            
    print("Deduplicating records...")
    unique, duplicates = deduplicate_records(validated)
    print(f"Found {len(unique)} unique records, {len(duplicates)} duplicates.")
    
    print(f"Saving normalized records to {normalized_dir}...")
    normalized_dir.mkdir(exist_ok=True)
    
    for record in unique:
        output_file = normalized_dir / f"{record.id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(record.model_dump_json(indent=2))
            
    print(f"Saved {len(unique)} files to {normalized_dir}.")
    
    stats = generate_statistics(unique)
    print_statistics(stats)
    
    stats_file = base_dir / "statistics.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    print("--- Pipeline completed successfully ---")

if __name__ == "__main__":
    main()
