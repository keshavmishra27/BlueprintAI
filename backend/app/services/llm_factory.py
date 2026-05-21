import os
import logging
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from crewai import LLM
load_dotenv(override=True)
os.environ.setdefault("OPENAI_API_KEY", "dummy_key_to_prevent_crewai_crash")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def check_llm_availability():
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key and google_key != "your_gemini_api_key_here":
        logger.info("Cloud LLM (Google Gemini) detected via GOOGLE_API_KEY.")
        return
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key and openrouter_key != "your_openrouter_api_key_here":
        logger.info("Cloud LLM (OpenRouter) detected via OPENROUTER_API_KEY.")
        return
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    try:
        import requests
        r = requests.get(f"{base_url}/api/tags", timeout=3)
        if r.status_code != 200:
             raise Exception(f"Ollama returned status {r.status_code}")
        models = [m["name"] for m in r.json().get("models", [])]
        if not any(m.startswith(model.split(":")[0]) for m in models):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail=f"Model '{model}' not found in Ollama. Run: ollama pull {model}",
            )
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Ollama check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Ollama is not running and no cloud API keys were found. Start Ollama with: ollama serve ({e})",
        )
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")
OPENROUTER_FALLBACK_MODEL = os.getenv("OPENROUTER_FALLBACK_MODEL", "gpt-4o-mini")
OPENROUTER_CREW_MODEL = os.getenv("OPENROUTER_CREW_MODEL", OPENROUTER_FALLBACK_MODEL)
OPENROUTER_FALLBACK_MAX_TOKENS = int(os.getenv("OPENROUTER_FALLBACK_MAX_TOKENS", "466"))
OPENROUTER_CREW_MAX_TOKENS = int(os.getenv("OPENROUTER_CREW_MAX_TOKENS", "4096"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1500"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
logger.info("LLM Factory initialized (OpenRouter=%s, max_tokens=%s, crew_max_tokens=%s)", "yes" if OPENROUTER_API_KEY else "no", LLM_MAX_TOKENS, OPENROUTER_CREW_MAX_TOKENS)
def extract_json_from_text(text: str) -> dict:
    if not text:
        return {}
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    if start != -1:
        end = text.rfind("}")
        if end != -1 and end > start:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                open_braces = json_str.count("{")
                close_braces = json_str.count("}")
                if open_braces > close_braces:
                    fixed_json = json_str + ("}" * (open_braces - close_braces))
                    try:
                        return json.loads(fixed_json)
                    except:
                        pass
                try:
                    for suffix in ["}", "]}", "}}", "}]}", "}]}}"]:
                         try:
                             return json.loads(json_str + suffix)
                         except:
                             continue
                except:
                    pass
    return {}

def _parse_openrouter_available_tokens(error: Exception) -> int | None:
    if not error:
        return None
    text = str(error)
    match = re.search(r"can only afford (\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"you requested up to \d+ tokens, but can only afford (\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def _google_llm(temperature=0.7):
    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key or google_key == "your_gemini_api_key_here":
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
        return ChatGoogleGenerativeAI(model=model, google_api_key=google_key, temperature=temperature)
    except Exception as e:
        logger.warning("Google Gemini init failed: %s", e)
        return None


def get_hybrid_llm(temperature=0.7):
    llms = []
    gemini = _google_llm(temperature)
    if gemini:
        llms.append(gemini)
    has_key = bool(OPENROUTER_API_KEY) and OPENROUTER_API_KEY != "your_openrouter_api_key_here"
    if has_key:
        try:
            logger.info(f"Initializing OpenRouter with model {OPENROUTER_MODEL}")
            openrouter = ChatOpenAI(
                model=OPENROUTER_MODEL,
                openai_api_key=OPENROUTER_API_KEY,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=temperature,
                max_tokens=LLM_MAX_TOKENS,
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Group Maker"
                }
            )
            llms.append(openrouter)
            logger.info("OpenRouter primary model added to LLM list")
        except Exception as e:
            logger.warning(f"Primary OpenRouter model {OPENROUTER_MODEL} failed to initialize: {e}")
        if OPENROUTER_FALLBACK_MODEL and OPENROUTER_FALLBACK_MODEL != OPENROUTER_MODEL:
            try:
                logger.info(f"Initializing OpenRouter fallback model {OPENROUTER_FALLBACK_MODEL} with max_tokens={OPENROUTER_FALLBACK_MAX_TOKENS}")
                openrouter_fallback = ChatOpenAI(
                    model=OPENROUTER_FALLBACK_MODEL,
                    openai_api_key=OPENROUTER_API_KEY,
                    openai_api_base="https://openrouter.ai/api/v1",
                    temperature=temperature,
                    max_tokens=OPENROUTER_FALLBACK_MAX_TOKENS,
                    default_headers={
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "Group Maker"
                    }
                )
                llms.append(openrouter_fallback)
                logger.info("OpenRouter fallback model added to LLM list")
            except Exception as e:
                logger.error(f"Failed to initialize OpenRouter fallback model {OPENROUTER_FALLBACK_MODEL}: {e}")
    else:
        logger.warning(f"Skipping OpenRouter: OPENROUTER_API_KEY is missing or invalid.")
    logger.info(f"Adding Ollama ({OLLAMA_MODEL}) to LLM list")
    ollama = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        max_tokens=LLM_MAX_TOKENS
    )
    llms.append(ollama)
    return llms
def invoke_hybrid_llm(messages, temperature=0.7, max_retries=3):
    llms = get_hybrid_llm(temperature)
    logger.info(f"Hybrid LLM: Attempting invocation with {len(llms)} models in priority list (Retries: {max_retries}).")
    last_exception = None
    for llm in llms:
        model_name = getattr(llm, "model_name", getattr(llm, "model", "Unknown"))
        current_max_tokens = LLM_MAX_TOKENS
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt+1}/{max_retries} with {model_name} (max_tokens={current_max_tokens})")
                response = llm.invoke(messages, config={"timeout": LLM_TIMEOUT, "max_tokens": current_max_tokens})
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
                available = _parse_openrouter_available_tokens(e)
                if available and available < current_max_tokens:
                    logger.info(f"OpenRouter credit limit detected, retrying with max_tokens={available}")
                    current_max_tokens = available
                    continue
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} attempts failed for {model_name}. Moving and falling back...")
                continue
    raise last_exception or Exception("All LLMs failed to respond after multiple retries")
def get_hybrid_crew_llm():
    # 1. Try Google Gemini first
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key and google_key != "your_gemini_api_key_here":
        model = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
        logger.info("Configuring CrewAI for Google Gemini (%s)", model)
        return LLM(model=f"gemini/{model}", api_key=google_key)

    # 2. Try OpenRouter
    has_key = bool(OPENROUTER_API_KEY) and OPENROUTER_API_KEY != "your_openrouter_api_key_here"
    if has_key:
        crew_model = OPENROUTER_CREW_MODEL
        try:
            logger.info(
                "Configuring CrewAI for OpenRouter (model=%s, max_tokens=%s)",
                crew_model, OPENROUTER_CREW_MAX_TOKENS,
            )
            llm = LLM(
                model=f"openai/{crew_model}",
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY,
                timeout=max(LLM_TIMEOUT, 120),
                max_completion_tokens=OPENROUTER_CREW_MAX_TOKENS,
            )
            return llm
        except Exception as e:
            logger.warning(f"OpenRouter crew LLM init failed: {e}. Falling back to Ollama.")

    # 3. Fallback to Ollama (always available as last resort)
    logger.info(f"Configuring CrewAI for Ollama ({OLLAMA_MODEL})")
    return LLM(
        model=f"ollama/{OLLAMA_MODEL}",
        base_url=f"{OLLAMA_BASE_URL}",
        api_key="ollama",
        timeout=LLM_TIMEOUT,
        max_completion_tokens=LLM_MAX_TOKENS,
    )