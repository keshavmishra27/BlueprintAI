import json
import sys
from pathlib import Path

def print_public_scenario(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    print(f"=== PUBLIC SCENARIO: {filepath} ===")
    print(f"Problem: {data.get('problem')}")
    print(f"Context: {data.get('context')}")
    print("Constraints:")
    for c in data.get('known_constraints', []):
        print(f"  - {c}")
    print("Requirements:")
    for r in data.get('known_requirements', []):
        print(f"  - {r}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python show_public_scenario.py <path_to_json>")
        sys.exit(1)
    print_public_scenario(sys.argv[1])
