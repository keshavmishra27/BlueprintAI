import io
import logging
import os
import zipfile
from urllib.parse import urlparse
import requests as http_requests
from dotenv import load_dotenv
logger = logging.getLogger(__name__)
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".scss",
    ".java", ".go", ".cpp", ".c", ".h",
    ".rs", ".rb", ".php", ".swift", ".kt", ".sh",
}
PRIORITY_FILENAMES = {
    "readme.md", "pyproject.toml", "package.json", "requirements.txt",
    "dockerfile", "docker-compose.yml", "makefile",
}
MAX_FILE_SIZE_BYTES = 100_000
MAX_TOTAL_CHARS = 18_000
def _truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[...truncated due prompt size limit...]\n"
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
def download_repo_zip(owner: str, repo: str) -> bytes:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/HEAD"
    resp = http_requests.get(api_url, headers=_get_api_headers(), timeout=30, stream=True)
    if resp.status_code != 200:
        raise ValueError(f"Failed to download repository archive: {resp.status_code}")
    return resp.content
def _should_read(path: str, size: int) -> bool:
    parts = path.split("/", 1)
    if len(parts) < 2:
        return False
    clean_path = parts[1]
    ext = os.path.splitext(clean_path)[1].lower()
    filename = os.path.basename(clean_path).lower()
    return (ext in CODE_EXTENSIONS or filename in PRIORITY_FILENAMES) and size <= MAX_FILE_SIZE_BYTES
def _gather_code_from_zip(zip_bytes: bytes) -> str:
    zip_io = io.BytesIO(zip_bytes)
    aggregated = []
    total_chars = 0
    with zipfile.ZipFile(zip_io) as z:
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
def _summarize_repo_structure(zip_bytes: bytes) -> dict:
    summary = {
        "total_files": 0,
        "source_files": 0,
        "python_files": 0,
        "has_readme": False,
        "has_package_metadata": False,
        "has_tests": False,
        "has_ci": False,
        "has_notebooks": False,
        "top_level_scripts": 0,
    }
    zip_io = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(zip_io) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            path = info.filename
            clean_path = path.split("/", 1)[1] if "/" in path else path
            filename = os.path.basename(clean_path).lower()
            ext = os.path.splitext(clean_path)[1].lower()
            summary["total_files"] += 1
            if ext in CODE_EXTENSIONS:
                summary["source_files"] += 1
            if filename.endswith(".py"):
                summary["python_files"] += 1
            if filename == "readme.md":
                summary["has_readme"] = True
            if filename in {"requirements.txt", "pyproject.toml", "setup.py", "package.json", "environment.yml", "conda.yml"}:
                summary["has_package_metadata"] = True
            if "/tests/" in clean_path.lower() or filename.startswith("test_") or filename.endswith("_test.py"):
                summary["has_tests"] = True
            if clean_path.lower().startswith(".github/workflows/") or filename in {"ci.yml", "ci.yaml", "azure-pipelines.yml", "circle.yml"}:
                summary["has_ci"] = True
            if ext == ".ipynb":
                summary["has_notebooks"] = True
            if "/" not in clean_path and filename.endswith(".py"):
                summary["top_level_scripts"] += 1
    likely_tutorial = (
        summary["source_files"] <= 6
        and not summary["has_tests"]
        and not summary["has_ci"]
        and not summary["has_package_metadata"]
    )
    summary["likely_tutorial"] = likely_tutorial
    return summary
def _format_repo_summary(info: dict) -> str:
    lines = [
        f"Total files: {info.get('total_files', 0)}",
        f"Source files: {info.get('source_files', 0)}",
        f"Python files: {info.get('python_files', 0)}",
        f"Has README: {'yes' if info.get('has_readme') else 'no'}",
        f"Has package metadata: {'yes' if info.get('has_package_metadata') else 'no'}",
        f"Has tests: {'yes' if info.get('has_tests') else 'no'}",
        f"Has CI/workflows: {'yes' if info.get('has_ci') else 'no'}",
        f"Has notebooks: {'yes' if info.get('has_notebooks') else 'no'}",
        f"Top-level Python scripts: {info.get('top_level_scripts', 0)}",
    ]
    if info.get("likely_tutorial"):
        lines.append("Judgment: likely a small tutorial/miniproject.")
    return "\n".join(lines)
def _score_value(score_data):
    if isinstance(score_data, dict):
        return float(score_data.get("score", 0))
    if isinstance(score_data, (int, float)):
        return float(score_data)
    return 0.0
def _recalculate_total_score(scores: dict) -> float:
    weights = {
        'functionality': 0.25, 'code_quality': 0.20,
        'documentation': 0.15, 'architecture': 0.15,
        'testing_ci': 0.10, 'innovation_ux': 0.15,
    }
    ws_sum = 0.0
    w_sum = 0.0
    for dim, dw in weights.items():
        value = scores.get(dim)
        if value is None:
            continue
        score = _score_value(value)
        weight = float(value.get('weight', dw)) if isinstance(value, dict) else dw
        ws_sum += score * weight
        w_sum += weight
    return round((ws_sum / w_sum) * 10, 1) if w_sum > 0 else 0.0
def _adjust_simple_project_scores(result: dict, repo_info: dict) -> dict:
    if not repo_info.get("likely_tutorial"):
        return result
    scores = result.get("scores")
    if not isinstance(scores, dict):
        return result
    caps = {
        "architecture": 3.0,
        "testing_ci": 1.0,
        "innovation_ux": 2.0,
        "documentation": 4.0,
    }
    adjusted = False
    for key, cap in caps.items():
        score_data = scores.get(key)
        score_value = _score_value(score_data)
        if score_value > cap:
            adjusted = True
            if isinstance(score_data, dict):
                score_data["score"] = cap
            else:
                scores[key] = {"score": cap, "weight": caps.get(key, 0), "reasons": []}
    if adjusted:
        result["scores"] = scores
        result["total_score"] = _recalculate_total_score(scores)
        mentor_notes = result.get("mentor_notes", "")
        note = (
            "Note: repository metadata indicates a small tutorial/miniproject. "
            "Dimension scores have been capped to reflect expected complexity."
        )
        result["mentor_notes"] = (mentor_notes + "\n\n" + note).strip() if mentor_notes else note
    return result
def analyze_repo(github_url: str, student_name: str) -> dict:
    owner, repo = _parse_github_url(github_url)
    zip_bytes = download_repo_zip(owner, repo)
    code_dump = _gather_code_from_zip(zip_bytes)
    if not code_dump.strip():
        raise ValueError("No readable code files found in this repository or access limit reached.")
    from backend.app.services.static_analysis_service import run_static_analysis
    from backend.app.services.crews.repo_crew import run_repo_judge_crew
    static_summary = run_static_analysis(zip_bytes)
    repo_info = _summarize_repo_structure(zip_bytes)
    repo_summary = _format_repo_summary(repo_info)
    result = run_repo_judge_crew(
        github_url=github_url,
        student_name=student_name,
        code_dump=code_dump,
        static_summary=static_summary,
        repo_summary=repo_summary,
    )
    return _adjust_simple_project_scores(result, repo_info)
def analyze_repo_llm_only(
    github_url: str,
    student_name: str,
    code_dump: str,
    static_summary: dict,
    repo_summary: str = "",
    repo_info: dict | None = None,
) -> dict:
    """Direct LLM fallback when Crew fails."""
    from backend.app.services.llm_factory import invoke_hybrid_llm, extract_json_from_text
    from backend.app.routers.repo_judge import JUDGE_JSON_SCHEMA
    from langchain_core.messages import SystemMessage, HumanMessage
    import json
    from backend.app.routers.repo_judge import SCORING_RUBRIC
    system_prompt = (
        "You are a hackathon judge. Static analysis + code sample provided.\n"
        "Return ONLY valid JSON — no markdown fences, no explanation, no extra text.\n\n"
        "CRITICAL TYPE RULES (violating these causes a system crash):\n"
        "- \"accessibility\" must be a STRING (e.g. \"public\"), never a dict\n"
        "- \"mentor_notes\" must be a STRING paragraph, never a list\n"
        "- \"coding_style_summary\" must be a STRING paragraph, never a list\n"
        "- Each score in \"scores\" must be an OBJECT with keys \"score\" (number), "
        "\"weight\" (number), and \"reasons\" (LIST of strings, never a single string)\n"
        "- \"reproducibility\" must be an OBJECT with \"can_run\" (bool), "
        "\"run_commands\" (list of strings), and \"notes\" (string)\n"
        "- \"files\" inside top_issues must be a list of OBJECTS with \"path\" and \"lines\" keys, "
        "never plain strings\n"
        "- \"hackathon_recommendations\" must be a list of OBJECTS suggesting 2-3 real-world upcoming or recurring corporate/global hackathons (e.g., MLH, specific company hackathons) where this project would be a great fit.\n\n"
        "Use the scoring rubric below to differentiate simple tutorial projects from full-stack or innovative solutions. "
        "Do not give every repo the same mid-range score.\n\n"
        f"{SCORING_RUBRIC}\n\n"
        f"EXACT JSON SCHEMA TO FOLLOW:\n{JUDGE_JSON_SCHEMA}"
    )
    user_prompt = (
        f"Repo: {github_url}\nStudent: {student_name}\n"
        f"REPO METADATA:\n{_truncate_text(repo_summary, 900)}\n\n"
        f"STATIC:\n{_truncate_text(json.dumps(static_summary), 3000)}\n\n"
        f"CODE:\n{_truncate_text(code_dump, 12000)}"
    )
    try:
        response = invoke_hybrid_llm(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
            temperature=0.3,
        )
        raw = response.content.strip()
        result = extract_json_from_text(raw)
        if result and "scores" in result:
            result["repo_url"] = github_url
            result["student_name"] = student_name
            result["static_analysis"] = static_summary
            return result
    except Exception as e:
        logger.error("LLM fallback failed: %s", e)
    result = _error_result(github_url, student_name, "Analysis incomplete")
    if repo_info:
        return _adjust_simple_project_scores(result, repo_info)
    return result
def _error_result(github_url, student_name, detail):
    return {
        "repo_url": github_url,
        "accessibility": "error",
        "languages": [],
        "scores": {
            "functionality": {"score": 0, "reasons": [detail]},
            "code_quality": {"score": 0, "reasons": []},
            "documentation": {"score": 0, "reasons": []},
            "architecture": {"score": 0, "reasons": []},
            "testing_ci": {"score": 0, "reasons": []},
            "innovation_ux": {"score": 0, "reasons": []},
        },
        "total_score": 0,
        "strengths": [],
        "top_issues": [{"severity": "critical", "title": "Analysis Incomplete", "description": detail, "files": []}],
        "reproducibility": {"can_run": False, "notes": detail},
        "mentor_notes": detail,
        "student_name": student_name,
    }
