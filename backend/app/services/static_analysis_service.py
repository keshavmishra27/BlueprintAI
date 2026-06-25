import json
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from io import BytesIO
logger = logging.getLogger(__name__)
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb", ".php",
}
def run_static_analysis(zip_bytes: bytes) -> dict:
    """Extract zip to temp dir and run ruff + bandit when available."""
    summary = {
        "ruff": None,
        "bandit": None,
        "tools_available": [],
        "notes": [],
    }
    with tempfile.TemporaryDirectory(prefix="repo_static_") as tmp:
        root = _extract_zip(zip_bytes, tmp)
        if not root:
            summary["notes"].append("Could not extract repository archive.")
            return summary
        py_root = _find_python_root(root)
        if shutil.which("ruff"):
            summary["tools_available"].append("ruff")
            summary["ruff"] = _run_ruff(py_root)
        else:
            summary["notes"].append("ruff not installed — skipped lint pass.")
        if shutil.which("bandit"):
            summary["tools_available"].append("bandit")
            summary["bandit"] = _run_bandit(py_root)
        else:
            summary["notes"].append("bandit not installed — skipped security pass.")
    return summary
def _extract_zip(zip_bytes: bytes, tmp: str) -> str | None:
    try:
        with zipfile.ZipFile(BytesIO(zip_bytes)) as z:
            z.extractall(tmp)
        entries = [os.path.join(tmp, e) for e in os.listdir(tmp)]
        if len(entries) == 1 and os.path.isdir(entries[0]):
            return entries[0]
        return tmp
    except Exception as e:
        logger.warning("Zip extract failed: %s", e)
        return None
def _find_python_root(root: str) -> str:
    for dirpath, _, files in os.walk(root):
        if any(f.endswith(".py") for f in files):
            return root
    return root
def _run_ruff(path: str) -> dict:
    try:
        proc = subprocess.run(
            ["ruff", "check", path, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        issues = json.loads(proc.stdout) if proc.stdout.strip().startswith("[") else []
        return {
            "issue_count": len(issues),
            "sample": issues[:15],
            "exit_code": proc.returncode,
        }
    except Exception as e:
        return {"error": str(e)}
def _run_bandit(path: str) -> dict:
    try:
        proc = subprocess.run(
            ["bandit", "-r", path, "-f", "json", "-q"],
            capture_output=True,
            text=True,
            timeout=90,
        )
        data = json.loads(proc.stdout) if proc.stdout.strip() else {}
        results = data.get("results", [])
        return {
            "issue_count": len(results),
            "sample": results[:15],
            "exit_code": proc.returncode,
        }
    except Exception as e:
        return {"error": str(e)}
