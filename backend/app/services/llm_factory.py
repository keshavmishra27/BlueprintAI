import os
import logging
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from crewai import LLM

load_dotenv(override=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

logger.info(f"LLM Factory initialized.")
logger.info(f"DEBUG: OPENROUTER_API_KEY is {'SET' if OPENROUTER_API_KEY else 'NOT SET'}")
if OPENROUTER_API_KEY:
    logger.info(f"DEBUG: Key length: {len(OPENROUTER_API_KEY)}")
    logger.info(f"DEBUG: Key starts with: {OPENROUTER_API_KEY[:10]}...")

def extract_json_from_text(text: str) -> dict:
    """
    Robustly extracts JSON from LLM output.
    Supports markdown blocks and loose text.
    """
    if not text:
        return {}
    
    # 1. Try extracting content within ```json ... ``` or ``` ... ```
    # Using a non-greedy approach for the content but being careful with DOTALL
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            # If the block itself is malformed (e.g. missing closing brace inside the block)
            # we'll fall through to the more aggressive text search
            pass

    # 2. Try finding the first '{' and the last '}' that could be a JSON object
    # We look for the first '{' and then try to find a matching '}' or the last one
    start = text.find("{")
    if start != -1:
        # Search from the end for the last '}'
        end = text.rfind("}")
        if end != -1 and end > start:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # If standard parsing fails, try to fix common truncation issues 
                
                # Simple balancing of braces
                open_braces = json_str.count("{")
                close_braces = json_str.count("}")
                
                if open_braces > close_braces:
                    fixed_json = json_str + ("}" * (open_braces - close_braces))
                    try:
                        return json.loads(fixed_json)
                    except:
                        pass
                
                # Try finding any sub-JSON if the whole block is mangled
                # This is a bit risky but can help with large responses
                try:
                    # Look for the last valid JSON-like structure if it was truncated mid-object
                    # We'll just try to "stich" it by adding closing characters in order
                    for suffix in ["}", "]}", "}}", "}]}", "}]}}"]:
                         try:
                             return json.loads(json_str + suffix)
                         except:
                             continue
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
    
    # Add OpenRouter if key is set
    has_key = bool(OPENROUTER_API_KEY) and OPENROUTER_API_KEY != "your_openrouter_api_key_here"
    
    if has_key:
        try:
            logger.info(f"Initializing OpenRouter with model {OPENROUTER_MODEL}")
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
            logger.info("OpenRouter added to LLM list")
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter: {e}")
    else:
        logger.warning(f"Skipping OpenRouter: OPENROUTER_API_KEY is missing or invalid.")

    # Always add Ollama as fallback
    logger.info(f"Adding Ollama ({OLLAMA_MODEL}) to LLM list")
    ollama = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature
    )
    llms.append(ollama)
    
    return llms

def invoke_hybrid_llm(messages, temperature=0.7, max_retries=3):
    """Try OpenRouter first, then fall back to Ollama. Each with retries."""
    llms = get_hybrid_llm(temperature)
    logger.info(f"Hybrid LLM: Attempting invocation with {len(llms)} models in priority list (Retries: {max_retries}).")
    
    last_exception = None
    for llm in llms:
        model_name = getattr(llm, "model_name", getattr(llm, "model", "Unknown"))
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt+1}/{max_retries} with {model_name}")
                # Set a strict timeout to prevent hanging
                response = llm.invoke(messages, config={"timeout": 60})
                
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
                logger.warning(f"Attempt {attempt+1} failed for {model_name}: {e}")
                last_exception = e
                # If it's the last attempt for this model, move to next model
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} attempts failed for {model_name}. Moving and falling back...")
                continue
            
    raise last_exception or Exception("All LLMs failed to respond after multiple retries")

def get_hybrid_crew_llm():
    """Returns a CrewAI LLM configured with OpenRouter priority or Ollama fallback."""
    has_key = bool(OPENROUTER_API_KEY) and OPENROUTER_API_KEY != "your_openrouter_api_key_here"
    
    if has_key:
        logger.info(f"Configuring CrewAI for OpenRouter ({OPENROUTER_MODEL})")
        return LLM(
            model=f"openai/{OPENROUTER_MODEL}",
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
    else:
        logger.info(f"Configuring CrewAI for Ollama ({OLLAMA_MODEL})")
        return LLM(
            model=OLLAMA_MODEL,
            base_url=f"{OLLAMA_BASE_URL}/v1",
            api_key="ollama"
        )
