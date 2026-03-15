import os
import logging
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from crewai import LLM

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def extract_json_from_text(text: str) -> dict:
    """
    Robustly extracts JSON from LLM output.
    Supports markdown blocks and loose text.
    """
    if not text:
        return {}
    
    # 1. Try extracting content within ```json ... ``` or ``` ... ```
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 2. Try finding the first '{' and last '}'
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        json_str = text[start:end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # If standard parsing fails, try to fix common truncation issues 
            # (only if it ends abruptly)
            if not json_str.endswith("}"):
                 json_str += "}"
            
            # Simple balancing of braces as a last resort
            open_braces = json_str.count("{")
            close_braces = json_str.count("}")
            if open_braces > close_braces:
                json_str += "}" * (open_braces - close_braces)
            
            try:
                return json.loads(json_str)
            except:
                pass

    return {}

def get_hybrid_llm(temperature=0.7):
    """
    Returns a list of LLMs in priority order.
    1. OpenRouter (if API key available)
    2. Ollama
    """
    llms = []
    
    # Add OpenRouter if key exists
    if OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_openrouter_api_key_here":
        try:
            openrouter = ChatOpenAI(
                model=OPENROUTER_MODEL,
                openai_api_key=OPENROUTER_API_KEY,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=temperature,
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Group Maker"
                }
            )
            llms.append(openrouter)
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter: {e}")

    # Always add Ollama as fallback
    ollama = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature
    )
    llms.append(ollama)
    
    return llms

def invoke_hybrid_llm(messages, temperature=0.7):
    """Try OpenRouter first, then fall back to Ollama."""
    llms = get_hybrid_llm(temperature)
    
    last_exception = None
    for llm in llms:
        try:
            model_name = getattr(llm, "model_name", getattr(llm, "model", "Unknown"))
            logger.info(f"Attempting invocation with {model_name}")
            response = llm.invoke(messages)
            
            # Normalize content to string
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
            logger.warning(f"Failed to invoke {model_name}: {e}")
            last_exception = e
            continue
            
    raise last_exception or Exception("All LLMs failed to respond")

def get_hybrid_crew_llm():
    """Returns a CrewAI LLM configured with OpenRouter priority or Ollama fallback."""
    if OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_openrouter_api_key_here":
        return LLM(
            model=f"openai/{OPENROUTER_MODEL}",
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
    else:
        return LLM(
            model=OLLAMA_MODEL,
            base_url=f"{OLLAMA_BASE_URL}/v1",
            api_key="ollama"
        )
