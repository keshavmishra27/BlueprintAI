import json
from pathlib import Path
from typing import List, Dict, Any

def ingest_raw_data(raw_dir: Path) -> List[Dict[str, Any]]:
    """Reads all JSON files from the raw directory."""
    raw_records = []
    if not raw_dir.exists():
        return raw_records
        
    for filepath in raw_dir.glob("**/*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    raw_records.extend(data)
                elif isinstance(data, dict):
                    raw_records.append(data)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            
    return raw_records
