import sys
import os
from dotenv import load_dotenv
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)
dotenv_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path)
from backend.app.services.llm_factory import invoke_hybrid_llm, GOOGLE_API_KEY
from langchain_core.messages import HumanMessage
import logging
logging.basicConfig(level=logging.INFO)
def test_fallback():
    print(f"Project root: {root_dir}")
    print(f"Loading .env from: {dotenv_path}")
    print(f"GOOGLE_API_KEY (first 5 chars): {str(GOOGLE_API_KEY)[:5]}...")
    print(f"GEMINI_MODEL: {os.getenv('GEMINI_MODEL')}")
    print("\nTesting Hybrid LLM Fallback (should prefer Gemini)...")
    messages = [HumanMessage(content="Say 'Ollama Fallback' if you are Ollama, or 'Gemini Active' if you are Gemini.")]
    try:
        response = invoke_hybrid_llm(messages)
        print(f"\nResponse: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
if __name__ == "__main__":
    test_fallback()