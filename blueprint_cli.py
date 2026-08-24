import sys
import argparse
from pathlib import Path

from product.service import ProductService

def main():
    parser = argparse.ArgumentParser(description="BlueprintAI CLI Adapter")
    parser.add_argument("command", choices=["analyze"])
    parser.add_argument("--idea", required=True, help="Natural language description of the architecture")
    parser.add_argument("--repo", required=True, help="Path to the repository to analyze")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        service = ProductService()
        print(f"Analyzing idea: {args.idea}")
        print(f"Against repository: {args.repo}")
        print("...")
        
        result = service.analyze(args.idea, args.repo)
        
        print("\nArchitecture Decision")
        print("────────────────────────")
        print(f"Winner: {result.architecture_decision.winning_path_id}")
        
        print("\nExpected Architecture")
        print("──────────────────────")
        for comp in result.architecture_decision.components:
            print(f"- {comp}")
            
        print("\nRepository Architecture")
        print("────────────────────────")
        for comp in result.repository_architecture.components:
            print(f"- {comp}")
            
        print("\nGap Report")
        print("────────────────────────")
        
        counts = {"MATCH": 0, "MISSING": 0, "MISMATCH": 0, "EXTRA": 0, "UNKNOWN": 0, "CONFLICT": 0}
        for f in result.gap_report.findings:
            counts[f.category.value] += 1
            print(f"[{f.category.value}] Expected: {f.expected} | Observed: {f.observed}")
            
        print("\nSummary:")
        for k, v in counts.items():
            print(f"{k.ljust(10)} {v}")
            
        print("\nGovernance")
        print("────────────────────────")
        if result.architecture_decision.governance:
            print(f"Status: {result.architecture_decision.governance.get('status', 'VALID')}")
        else:
            print("Status: VALID")

if __name__ == "__main__":
    main()
