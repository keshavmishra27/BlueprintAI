import os
import logging
import json
import base64
import io
import zipfile
from urllib.parse import urlparse
import requests as http_requests
from dotenv import load_dotenv
logger = logging.getLogger(__name__)
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
MAX_FILE_SIZE_BYTES = 100_000
MAX_TOTAL_CHARS     = 40_000
def _parse_github_url(url: str) -> tuple[str, str]:
    url = url.strip().rstrip("/")
    parsed = urlparse(url)
    if parsed.netloc not in ("github.com", "www.github.com"):
        raise ValueError("URL must be a github.com repository link.")
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError("Could not find owner/repo in the URL.")
    return parts[0], parts[1]
def _get_api_headers() -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers
def _should_read(path: str, size: int) -> bool:
    parts = path.split("/", 1)
    if len(parts) < 2: return False
    clean_path = parts[1]
    ext = os.path.splitext(clean_path)[1].lower()
    filename = os.path.basename(clean_path).lower()
    return (ext in CODE_EXTENSIONS or filename in PRIORITY_FILENAMES) and size <= MAX_FILE_SIZE_BYTES
def _gather_code(owner: str, repo: str) -> str:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/HEAD"
    headers = _get_api_headers()
    resp = http_requests.get(api_url, headers=headers, timeout=30, stream=True)
    if resp.status_code != 200:
        raise ValueError(f"Failed to download repository archive: {resp.status_code}")
    zip_bytes = io.BytesIO(resp.content)
    aggregated = []
    total_chars = 0
    with zipfile.ZipFile(zip_bytes) as z:
        file_infos = [info for info in z.infolist() if not info.is_dir()]
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
                clean_path = info.filename.split("/", 1)[1] if "/" in info.filename else info.filename
                snippet = content[: MAX_TOTAL_CHARS - total_chars]
                block = f"\n\n### FILE: {clean_path}\n```\n{snippet}\n```"
                aggregated.append(block)
                total_chars += len(block)
            except Exception:
                continue
    return "".join(aggregated)
def analyze_repo(github_url: str, student_name: str) -> dict:
    owner, repo = _parse_github_url(github_url)
    code_dump = _gather_code(owner, repo)
    if not code_dump.strip():
        raise ValueError("No readable code files found in this repository or access limit reached.")
    system_prompt = """You are an experienced international hackathon judge and technical mentor.
Input: a PUBLIC GitHub repository URL and its full codebase.
Your job: analyze the repository end-to-end and deliver an expert, actionable judging report.
### OUTPUT FORMAT (CRITICAL)
Return ONLY a JSON object followed by a short human summary.
The JSON must strictly follow this structure:
{
  "repo_url": "<url>",
  "accessibility": "public",
  "languages": ["python",...],
  "scores": {
    "functionality": {"score": 0-10, "reasons": []},
    "code_quality": {"score": 0-10, "reasons": []},
    "documentation": {"score": 0-10, "reasons": []},
    "architecture": {"score": 0-10, "reasons": []},
    "testing_ci": {"score": 0-10, "reasons": []},
    "innovation_ux": {"score": 0-10, "reasons": []}
  },
  "total_score": 0-100,
  "strengths": ["list top 3"],
  "top_issues": [
    {
      "severity": "major",
      "title": "Title",
      "description": "Detailed explanation and fix info",
      "files": [{"path":"filename.py","lines":"10-15"}],
      "estimated_effort_hours": 1.0
    }
  ],
  "security_warnings": [
    {
      "type": "secret_leak",
      "evidence": "file path or code snippet",
      "remediation": "how to fix"
    }
  ],
  "reproducibility": {"can_run": true, "notes": ""},
  "mentor_notes": "Constructive feedback (50-100 words)."
}
### CRITICAL: STRUCTURAL INTEGRITY
- "top_issues" and "security_warnings" MUST be lists of OBJECTS, not strings.
- Even for sparse repositories, provide structured objects.
### SCORING GUIDANCE
- 9-10: Production-grade; clean; tested; documented.
- 7-8: Very good; minor polish needed.
- 4-6: Functional but needs notable improvements.
- 1-3: Incomplete or brittle.
- 0: Non-functional or placeholder.
### CONSTRAINTS
- ALWAYS attach at least one file path for every major claim.
- Only include short code excerpts (≤3 lines) with line numbers.
- Be factual, constructive, and kind.
"""
    user_prompt = f"""Expert Hackathon Evaluation
===================
Student: {student_name}
Repository: https://github.com/{owner}/{repo}
FULL CODEBASE:
{code_dump}
Analyze this project as an expert judge. Return ONLY the JSON object followed by the human summary.
"""
    from .llm_factory import invoke_hybrid_llm, extract_json_from_text
    from langchain_core.messages import SystemMessage, HumanMessage
    try:
        response = invoke_hybrid_llm([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ], temperature=0.3)
        raw_full = response.content.strip() if hasattr(response, 'content') else str(response).strip()
    except Exception as e:
        logger.error(f"LLM Invocation failed: {e}")
        raw_full = ""
    result = extract_json_from_text(raw_full)
    if result and "scores" in result and isinstance(result["scores"], dict):
        potential_misplaced_keys = ["total_score", "mentor_notes", "strengths", "top_issues", "security_warnings", "reproducibility"]
        for key in potential_misplaced_keys:
            if key not in result and key in result["scores"]:
                logger.info(f"Recovered misplaced key '{key}' from 'scores' sub-object.")
                result[key] = result["scores"].pop(key)
    human_summary = ""
    if "```" in raw_full:
        parts = raw_full.split("```")
        if len(parts) > 2:
            human_summary = parts[-1].strip()
    required_keys = {"total_score", "scores", "mentor_notes"}
    is_valid_result = result and all(k in result for k in required_keys)
    if not is_valid_result:
        logger.error(f"Incomplete or invalid JSON from LLM. Raw response start: {raw_full[:500]}... (Total length: {len(raw_full)})")
        try:
            with open("llm_raw_debug.log", "w", encoding="utf-8") as f:
                f.write(raw_full)
        except:
            pass
    if is_valid_result:
        try:
            result["repo_url"] = github_url
            result["student_name"] = student_name
            if not human_summary and "mentor_notes" in result:
                 human_summary = result["mentor_notes"]
            return result
        except Exception as e:
            logger.error(f"Error post-processing JSON: {e}")
    error_detail = "Analysis Incomplete (AI response format issue)"
    if result and not is_valid_result:
        missing = required_keys - set(result.keys())
        error_detail = f"Incomplete AI response. Missing: {', '.join(missing)}"
    elif not result:
        error_detail = "No JSON found in AI response."
    return {
        "repo_url": github_url,
        "accessibility": "error",
        "languages": [],
        "scores": {
            "functionality": {"score": 0, "reasons": ["Analysis failed"]},
            "code_quality": {"score": 0, "reasons": []},
            "documentation": {"score": 0, "reasons": []},
            "architecture": {"score": 0, "reasons": []},
            "testing_ci": {"score": 0, "reasons": []},
            "innovation_ux": {"score": 0, "reasons": []}
        },
        "total_score": 0,
        "strengths": [],
        "top_issues": [
            {
                "severity": "critical",
                "title": "Analysis Incomplete",
                "description": f"The AI could not complete the analysis for this repository properly. {error_detail}",
                "estimated_effort_hours": 0,
                "files": []
            }
        ],
        "reproducibility": {"can_run": False, "notes": error_detail},
        "mentor_notes": f"The analysis failed: {error_detail}. This usually happens if the AI response is too large or malformed. Please try again.",
        "student_name": student_name
    }