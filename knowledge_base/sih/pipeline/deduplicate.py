from typing import List, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from schema.project import SIHProject

def deduplicate_records(records: List[SIHProject]) -> Tuple[List[SIHProject], List[SIHProject]]:
    """Deduplicates records based on ID and problem statement."""
    unique = []
    duplicates = []
    seen_ids = set()
    seen_problems = set()
    
    for record in records:
        is_dup = False
        
        if record.id in seen_ids:
            is_dup = True
        elif record.problem_statement and record.problem_statement.lower().strip() in seen_problems:
            is_dup = True
            
        if is_dup:
            duplicates.append(record)
        else:
            seen_ids.add(record.id)
            if record.problem_statement:
                seen_problems.add(record.problem_statement.lower().strip())
            unique.append(record)
            
    return unique, duplicates
