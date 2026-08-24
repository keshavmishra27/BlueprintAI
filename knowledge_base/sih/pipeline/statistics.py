from typing import List, Dict, Any
from collections import Counter
import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import schema
sys.path.append(str(Path(__file__).resolve().parent.parent))

from schema.project import SIHProject, OutcomeEnum

def generate_statistics(records: List[SIHProject]) -> Dict[str, Any]:
    stats = {
        "total_records": len(records),
        "verified_winners": sum(1 for r in records if r.outcome == OutcomeEnum.winner and r.outcome_verified),
        "editions_covered": dict(Counter(r.edition for r in records)),
        "domains_covered": dict(Counter(d for r in records for d in r.problem_domain)),
        "projects_with_problem_statement": sum(1 for r in records if r.problem_statement),
        "projects_with_solution_defined": sum(1 for r in records if r.what and r.how),
        "projects_with_technical_info": sum(1 for r in records if r.technical_approach or r.technologies),
        "projects_with_measurable_impact": sum(1 for r in records if r.measurable_or_claimed_impact),
        "projects_with_only_one_source": sum(1 for r in records if len(r.sources) == 1),
        "projects_with_multiple_sources": sum(1 for r in records if len(r.sources) > 1),
        "projects_without_sources": sum(1 for r in records if len(r.sources) == 0)
    }
    return stats

def print_statistics(stats: Dict[str, Any]):
    print("=== SIH Knowledge Base Statistics ===")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"\n{key.replace('_', ' ').title()}:")
            for k, v in value.items():
                print(f"  - {k}: {v}")
        else:
            print(f"{key.replace('_', ' ').title()}: {value}")
    print("=====================================")
