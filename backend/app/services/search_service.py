import json
import logging
from datetime import datetime, timezone

import requests

from backend.app.config import get_settings

logger = logging.getLogger(__name__)


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search the public web (DuckDuckGo) and GitHub repos. Returns cited snippets."""
    settings = get_settings()
    if not settings.search_enabled:
        return []

    results: list[dict] = []
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": item.get("title", ""),
                        "snippet": item.get("body", "")[:400],
                        "url": item.get("href", ""),
                        "source": "duckduckgo",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                    }
                )
    except Exception as e:
        logger.warning("DuckDuckGo search failed: %s", e)

    try:
        gh_q = requests.utils.quote(query)
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        r = requests.get(
            f"https://api.github.com/search/repositories?q={gh_q}&sort=stars&per_page=3",
            headers=headers,
            timeout=10,
        )
        if r.status_code == 200:
            for repo in r.json().get("items", [])[:3]:
                results.append(
                    {
                        "title": repo.get("full_name", ""),
                        "snippet": (repo.get("description") or "")[:400],
                        "url": repo.get("html_url", ""),
                        "source": "github",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                    }
                )
    except Exception as e:
        logger.warning("GitHub search failed: %s", e)

    return results


def format_search_context(results: list[dict]) -> str:
    if not results:
        return "No live search results available. State this in notes_and_limitations."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"[{i}] {r.get('title')} ({r.get('source')})\n"
            f"URL: {r.get('url')}\n"
            f"Snippet: {r.get('snippet')}\n"
            f"Retrieved: {r.get('date')}"
        )
    return "\n\n".join(lines)


def search_for_idea(idea: str) -> tuple[list[dict], str]:
    queries = [
        f"{idea[:80]} startup product",
        f"{idea[:80]} open source github",
        f"{idea[:80]} patent application",
    ]
    seen_urls: set[str] = set()
    merged: list[dict] = []
    for q in queries:
        for row in search_web(q, max_results=4):
            url = row.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(row)
    return merged, format_search_context(merged)
