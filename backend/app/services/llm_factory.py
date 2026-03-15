import os
import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from crewai import LLM

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_hybrid_llm(temperature=0.7):
    """
    Returns a list of LLMs in priority order.
    1. Gemini 1.5 Flash (if API key available)
    2. Ollama
    """
    llms = []
    
    # Add Gemini if key exists and is not the placeholder
    if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_gemini_api_key_here":
        try:
            gemini = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=temperature
            )
            llms.append(gemini)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    # Always add Ollama as fallback
    ollama = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature
    )
    llms.append(ollama)
    
    return llms

def invoke_hybrid_llm(messages, temperature=0.7):
    """Try Gemini first, then fall back to Ollama."""
    llms = get_hybrid_llm(temperature)
    
    last_exception = None
    for llm in llms:
        try:
            # Check if it's Gemini or Ollama for logging
            model_name = getattr(llm, "model", "Unknown")
            logger.info(f"Attempting invocation with {model_name}")
            response = llm.invoke(messages)
            
            # Normalize content to string if it's a list (common with newer Gemini models)
            if isinstance(response.content, list):
                text_parts = []
                for part in response.content:
                    if isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                    elif isinstance(part, str):
                        text_parts.append(part)
                response.content = "".join(text_parts)
                
            return response
        except Exception as e:
            logger.warning(f"Failed to invoke {getattr(llm, 'model', 'LLM')}: {e}")
            last_exception = e
            continue
            
    raise last_exception or Exception("All LLMs failed to respond")

def get_hybrid_crew_llm():
    """Returns a CrewAI LLM configured with Gemini priority or Ollama fallback."""
    if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_gemini_api_key_here":
        # CrewAI doesn't have a direct "hybrid" wrapper in the same sense, 
        # but we can return the best available one.
        return LLM(
            model=f"gemini/{GEMINI_MODEL}",
            api_key=GOOGLE_API_KEY
        )
    else:
        return LLM(
            model=OLLAMA_MODEL,
            base_url=f"{OLLAMA_BASE_URL}/v1",
            api_key="ollama"
        )
