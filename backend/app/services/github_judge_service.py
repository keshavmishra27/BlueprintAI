import os
import json
import base64
import io
import zipfile
from urllib.parse import urlparse

import requests as http_requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN",    "")

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".scss",
    ".java", ".go", ".cpp", ".c", ".h",
    ".rs", ".rb", ".php", ".swift", ".kt", ".sh",
}

PRIORITY_FILENAMES = {
    "readme.md", "pyproject.toml", "package.json", "requirements.txt",
    "dockerfile", "docker-compose.yml", "makefile"
}

MAX_FILE_SIZE_BYTES = 100_000 # Increased for better analysis
MAX_TOTAL_CHARS     = 40_000   # Increased logic context


def _parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL."""
    url = url.strip().rstrip("/")
    parsed = urlparse(url)
    if parsed.netloc not in ("github.com", "www.github.com"):
        raise ValueError("URL must be a github.com repository link.")
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError("Could not find owner/repo in the URL.")
    return parts[0], parts[1]


def _get_api_headers() -> dict:
    """Consolidated headers with optional token."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def _should_read(path: str, size: int) -> bool:
    """Decide whether to include a file based on extension and size."""
    # Remove the hash/prefix added by GitHub Zipball
    parts = path.split("/", 1)
    if len(parts) < 2: return False
    clean_path = parts[1]
    
    ext = os.path.splitext(clean_path)[1].lower()
    filename = os.path.basename(clean_path).lower()
    return (ext in CODE_EXTENSIONS or filename in PRIORITY_FILENAMES) and size <= MAX_FILE_SIZE_BYTES


def _gather_code(owner: str, repo: str) -> str:
    """Download the entire repo as a zipball and extract it in memory (FAST)."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/HEAD"
    headers = _get_api_headers()
    
    resp = http_requests.get(api_url, headers=headers, timeout=30, stream=True)
    if resp.status_code != 200:
        raise ValueError(f"Failed to download repository archive: {resp.status_code}")

    zip_bytes = io.BytesIO(resp.content)
    aggregated = []
    total_chars = 0

    with zipfile.ZipFile(zip_bytes) as z:
        # Get all files and their sizes
        file_infos = [info for info in z.infolist() if not info.is_dir()]
        
        # Sort for prioritization
        def sort_key(info):
            path = info.filename
            parts = path.split("/", 1)
            filename = os.path.basename(parts[1] if len(parts) > 1 else path).lower()
            priority = 0 if filename in PRIORITY_FILENAMES else 1
            return (priority, info.file_size)
        
        file_infos.sort(key=sort_key)

        for info in file_infos:
            if total_chars >= MAX_TOTAL_CHARS:
                aggregated.append("\n\n[...truncated — too many files to fit in context...]\n")
                break
            
            if not _should_read(info.filename, info.file_size):
                continue
            
            try:
                with z.open(info) as f:
                    content = f.read().decode("utf-8", errors="replace")
                
                # Remove the GitHub folder prefix from the path displayed to LLM
                clean_path = info.filename.split("/", 1)[1] if "/" in info.filename else info.filename
                
                snippet = content[: MAX_TOTAL_CHARS - total_chars]
                block = f"\n\n### FILE: {clean_path}\n```\n{snippet}\n```"
                aggregated.append(block)
                total_chars += len(block)
            except Exception:
                continue

    return "".join(aggregated)


def analyze_repo(github_url: str, student_name: str) -> dict:
    """
    Main entry point.
    1. Scrape the repo.
    2. Send code to Ollama.
    3. Return structured judge feedback.
    """
    owner, repo = _parse_github_url(github_url)

    code_dump = _gather_code(owner, repo)
    if not code_dump.strip():
        raise ValueError("No readable code files found in this repository or access limit reached.")

    system_prompt = """You are a STRICT judge panel member at Smart India Hackathon (SIH) — India's largest national-level hackathon run by the Government of India. You have judged 500+ teams. You are known for being rigorous, honest, and impossible to impress with surface-level work.

Your core philosophy:
- Most student projects are CRUD apps or tutorial clones in disguise. Call them out.
- A high score (80+) is RARE and reserved for projects with genuine innovation, real-world impact, and solid technical depth.
- You do NOT give marks for effort or good intentions — only for what is actually built.
- You MUST score harshly and justify every deduction.

SCORING RUBRIC (each dimension is 0–25, total 0–100):

1. CODE QUALITY (0-25):
   - 20-25: Clean architecture, SOLID principles, proper error handling, no hardcoding, production-like structure
   - 10-19: Decent structure but has issues (god functions, magic numbers, duplicated logic, poor naming)
   - 5-9:  Messy, procedural spaghetti, everything in one file, copy-pasted blocks
   - 0-4:  Tutorial-level code, no structure, hardcoded credentials, broken patterns

2. INNOVATION (0-25):
   - 20-25: Solves a real, specific problem in a novel way. Not just "an app that does X" — genuine creative engineering.
   - 10-19: Combines existing tools in a somewhat interesting way, but the core idea is not original
   - 5-9:  Clone of a common project (todo app, weather app, chat app, basic ML classifier, basic CRUD)
   - 0-4:  Textbook tutorial project with zero original contribution

3. COMPLETENESS (0-25):
   - 20-25: Core feature fully works end-to-end, edge cases handled, no obvious crashes, deployable
   - 10-19: Main flow works, but key features are missing, broken, or half-implemented
   - 5-9:  Skeleton or prototype — mostly UI/stubs with little working logic
   - 0-4:  Does not function, just boilerplate or empty files

4. DOCUMENTATION & PRESENTATION (0-25):
   - 20-25: Clear README with problem statement, architecture diagram, setup, demo screenshots/video
   - 10-19: Basic README but missing critical sections (no setup, no demo, no problem context)
   - 5-9:  Almost no README, no comments in code, a judge cannot understand what it does
   - 0-4:  Empty README or no README at all

PENALTY TRIGGERS (automatically deduct from innovation score):
- -8 if it's a basic CRUD app with no real intelligence or unique logic
- -8 if it's an ML project that just wraps a pre-trained model with no custom training/pipeline
- -5 if it has no real deployment or runnable demo

Return ONLY valid JSON. No markdown. No explanations outside the JSON. All improvements MUST be specific to files and include a correction step."""

    user_prompt = f"""SIH Judge Evaluation
====================
Student: {student_name}
Repository: https://github.com/{owner}/{repo}

FULL CODEBASE:
{code_dump}

As a strict SIH judge, evaluate this project honestly. Be specific. Reference actual file names and function names.
A score above 70 should be hard to achieve. Most student projects score 30–55.

Return ONLY this JSON object (absolutely no other text):
{{
  "overall_score": <integer 0-100, sum of the four dimensions>,
  "code_quality_score": <integer 0-25, per rubric>,
  "innovation_score": <integer 0-25, per rubric, after penalties>,
  "completeness_score": <integer 0-25, per rubric>,
  "documentation_score": <integer 0-25, per rubric>,
  "verdict": "<one brutally honest sentence — be direct, no sugarcoating>",
  "hackathon_readiness": "<2-3 sentences: Is this ready for an SIH demo? What would embarrass the student in front of judges? What is the single most important thing to fix BEFORE the hackathon?>",
  "strengths": [
    "<genuine strength with specific file/function reference — do NOT list things that are just 'basic'>"
  ],
  "improvements": [
    {{
      "file": "<path/to/file>",
      "issue": "<what exactly is wrong in this file>",
      "fix": "<step-by-step instructions or code snippet to fix it>"
    }}
  ],
  "standout_files": ["<path to the most impressive file, if any>"],
  "problem_areas": ["<path or area that is most problematic>", "<another problem area>"]
}}"""

    from .llm_factory import invoke_hybrid_llm
    from langchain_core.messages import SystemMessage, HumanMessage

    try:
        response = invoke_hybrid_llm([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ], temperature=0.3)
        raw = response.content.strip()
    except Exception as e:
        raw = f"Error calling LLM: {str(e)}"

    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        result = json.loads(raw)
        result["overall_score"] = (
            result.get("code_quality_score", 0) +
            result.get("innovation_score", 0) +
            result.get("completeness_score", 0) +
            result.get("documentation_score", 0)
        )
        result["repository"] = f"https://github.com/{owner}/{repo}"
        result["student_name"] = student_name
        return result
    except Exception:
        return {
            "overall_score": 0,
            "code_quality_score": 0,
            "innovation_score": 0,
            "completeness_score": 0,
            "documentation_score": 0,
            "verdict": "Could not parse LLM response.",
            "hackathon_readiness": raw[:500] if raw else "No response from LLM.",
            "strengths": ["None identified due to processing error."],
            "improvements": [
                {
                    "file": "General",
                    "issue": "The AI returned an unparseable response.",
                    "fix": "Please try again or check if the repository is too large."
                }
            ],
            "standout_files": [],
            "problem_areas": ["Processing failed."],
            "repository": f"https://github.com/{owner}/{repo}",
            "student_name": student_name,
        }
