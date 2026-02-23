"""
github_judge_service.py
-----------------------
Scrapes a public GitHub repository using the GitHub Contents API (no auth token needed),
aggregates the code files, and asks the local Ollama LLM to act as a hackathon judge.
"""

import os
import json
import base64
from urllib.parse import urlparse

import requests as http_requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Only real code files — skip docs/config to reduce LLM input size
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".scss",
    ".java", ".go", ".cpp", ".c", ".h",
    ".rs", ".rb", ".php", ".swift", ".kt", ".sh",
}

# Limits — keep input small for faster CPU inference
MAX_FILE_SIZE_BYTES = 30_000      # skip individual files larger than 30 KB
MAX_TOTAL_CHARS     = 30_000      # stop accumulating after 30 K chars


def _parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL. Raises ValueError on bad input."""
    url = url.strip().rstrip("/")
    parsed = urlparse(url)
    if parsed.netloc not in ("github.com", "www.github.com"):
        raise ValueError("URL must be a github.com repository link.")
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError("Could not find owner/repo in the URL.")
    return parts[0], parts[1]


def _get_file_tree(owner: str, repo: str) -> list[dict]:
    """Return the full recursive file tree from GitHub."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    headers = {"Accept": "application/vnd.github.v3+json"}
    resp = http_requests.get(api_url, headers=headers, timeout=15)
    if resp.status_code == 404:
        raise ValueError(f"Repository '{owner}/{repo}' not found or is private.")
    resp.raise_for_status()
    data = resp.json()
    return [item for item in data.get("tree", []) if item.get("type") == "blob"]


def _should_read(path: str, size: int) -> bool:
    """Decide whether to include a file based on extension and size."""
    ext = os.path.splitext(path)[1].lower()
    return ext in CODE_EXTENSIONS and size <= MAX_FILE_SIZE_BYTES


def _fetch_file_content(owner: str, repo: str, path: str) -> str | None:
    """Download and decode a single file from the GitHub Contents API."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    resp = http_requests.get(api_url, headers=headers, timeout=10)
    if resp.status_code != 200:
        return None
    data = resp.json()
    if data.get("encoding") == "base64":
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            return None
    return data.get("content")


def _gather_code(owner: str, repo: str) -> str:
    """Walk the file tree and concatenate readable code files."""
    tree = _get_file_tree(owner, repo)
    readable = [f for f in tree if _should_read(f.get("path", ""), f.get("size", 0))]

    aggregated = []
    total_chars = 0

    for file_info in readable:
        if total_chars >= MAX_TOTAL_CHARS:
            aggregated.append("\n\n[...truncated — too many files to fit in context...]\n")
            break
        path = file_info["path"]
        content = _fetch_file_content(owner, repo, path)
        if not content:
            continue
        snippet = content[: MAX_TOTAL_CHARS - total_chars]
        block = f"\n\n### FILE: {path}\n```\n{snippet}\n```"
        aggregated.append(block)
        total_chars += len(block)

    return "".join(aggregated)


def analyze_repo(github_url: str, student_name: str) -> dict:
    """
    Main entry point.
    1. Scrape the repo.
    2. Send code to Ollama.
    3. Return structured judge feedback.
    """
    owner, repo = _parse_github_url(github_url)

    # --- Gather code ---
    code_dump = _gather_code(owner, repo)
    if not code_dump.strip():
        raise ValueError("No readable code files found in this repository.")

    # --- Build LLM prompt ---
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

Return ONLY valid JSON. No markdown. No explanations outside the JSON."""

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
    "<specific, actionable fix with file/line reference where possible>",
    "<another specific fix>",
    "<another specific fix>"
  ],
  "standout_files": ["<path to the most impressive file, if any>"],
  "problem_areas": ["<path or area that is most problematic>", "<another problem area>"]
}}"""

    # --- Call Ollama ---
    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.3,
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    raw = response.content.strip()

    # Strip markdown fences if the model added them
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        result = json.loads(raw)
        # Recalculate total to be safe
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
        # Graceful fallback
        return {
            "overall_score": 0,
            "code_quality_score": 0,
            "innovation_score": 0,
            "completeness_score": 0,
            "documentation_score": 0,
            "verdict": "Could not parse LLM response.",
            "hackathon_readiness": raw[:500] if raw else "No response from LLM.",
            "strengths": [],
            "improvements": ["LLM returned an unparseable response — try again."],
            "standout_files": [],
            "problem_areas": [],
            "repository": f"https://github.com/{owner}/{repo}",
            "student_name": student_name,
        }
