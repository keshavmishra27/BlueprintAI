import subprocess
import time
import sys

def main():
    print("==================================================")
    print(" EXPERIMENT MODE B: TRUE ANTIGRAVITY              ")
    print("==================================================")
    
    print("\nTo run Mode B, you must act as the Agent Generative Runtime.")
    print("The deterministic Python engine must be running as a local server.")
    
    print("\n1. Start the FastAPI backend engine:")
    print("   Run: uvicorn backend.app.main:app --reload --port 8000")
    
    print("\n2. Provide the following prompt to your Antigravity Assistant:")
    print("-" * 50)
    print("Let's run BlueprintAI Experiment Mode B.")
    print("The API is running at http://localhost:8000")
    print("\nI have a messy project idea:")
    print("What: Predict patient wait times.")
    print("Why: Hospitals are overcrowded.")
    print("How: Use a massive LLM on cloud GPUs to analyze historical queue data.")
    print("\nConstraints:")
    print("- strict budget $500/mo")
    print("- no historical data")
    print("- no gpu instance")
    print("\nRequirements:")
    print("- Low cost")
    print("- High accuracy")
    print("\nPlease generate the initial ArchitectureNode and candidate AgentUncertainties.")
    print("Call POST /api/journey/start to evaluate them.")
    print("Based on the API's selected question, ask me the question.")
    print("When I answer, adapt the architecture and call POST /api/journey/answer.")
    print("Repeat until the API returns BEST_ARCHITECTURE_FOUND or NO_FEASIBLE_ARCHITECTURE_FOUND.")
    print("-" * 50)
    
    print("\n(Press Ctrl+C to exit this script. Run the uvicorn command manually to start the server.)")

if __name__ == "__main__":
    main()
