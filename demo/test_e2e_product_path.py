import os
import sys
import json
from pathlib import Path
from pprint import pprint

base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from idea_refiner.parsers.providers.groq import GroqProvider
from idea_refiner.parsers.llm import LLMIdeaParser
from idea_refiner.graph_generator.expander import GraphGenerator
from idea_refiner.orchestrator import Orchestrator
from decision_engine.tree.context import DecisionContext

def run_e2e():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("[SKIP] GROQ_API_KEY not set. Please set it to run the E2E test.")
        return

    print("==================================================")
    print("      E2E PRODUCT PATH TEST (LIVE LLM)            ")
    print("==================================================")
    
    idea = "A hospital overcrowding prediction system using patient flow data"
    print(f"User Idea: {idea}\n")
    
    provider = GroqProvider(api_key=api_key)
    parser = LLMIdeaParser(provider=provider)
    generator = GraphGenerator(provider=provider)
    orchestrator = Orchestrator(parser=parser, graph_generator=generator)
    
    context = DecisionContext(
        ontology_version="v1",
        registry_policy_hashes=[],
        environment_constraints=["Must be HIPAA compliant", "Real-time updates"],
        optimizer_preferences={
            "epistemic_lambda": 10.0,
            "cost_lambda": 0.5,
            "complexity_lambda": 0.5,
            "robustness_lambda": 20.0
        }
    )
    
    print("[1/5] Running LLM Parsing (Seeds)...")
    print("[2/5] Running Graph Expansion...")
    print("[3/5] Freezing Decision Graph...")
    print("[4/5] Running Ontology Evaluation & Optimizer...")
    print("[5/5] Generating Governance Report & Presentation...\n")
    
    try:
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            
        result = orchestrator.refine(idea, context)
        print("\n--- E2E RESULT ---")
        
        explanation = result.get("human_readable_explanation")
        if explanation:
            print("\n" + explanation + "\n")
        else:
            print("[Warning] No human readable explanation found in product response.")
            
        print("\n[PASS] E2E Pipeline completed successfully!")
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_e2e()
