from typing import List, Dict, Any, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from schema.project import SIHProject

def normalize_records(raw_records: List[Dict[str, Any]]) -> Tuple[List[SIHProject], List[Dict[str, Any]]]:
    """Validates and normalizes raw dicts into SIHProject Pydantic models."""
    validated = []
    errors = []
    
    for i, record in enumerate(raw_records):
        try:
            project = SIHProject(**record)
            validated.append(project)
        except Exception as e:
            errors.append({
                "record_id": record.get("id", f"unknown_index_{i}"),
                "error": str(e),
                "record": record
            })
            
    return validated, errors
