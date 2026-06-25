import json
import logging
import time
import re
from datetime import datetime, timezone
import requests
from backend.app.config import get_settings
logger = logging.getLogger(__name__)
_DDG_BACKOFF_SECONDS = 2.0  
_DDG_MAX_RETRIES = 3
def _search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """Search DuckDuckGo with retry/backoff for rate limits."""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        logger.warning("duckduckgo_search not installed")
        return []
    results: list[dict] = []
    backoff = _DDG_BACKOFF_SECONDS
    for attempt in range(1, _DDG_MAX_RETRIES + 1):
        try:
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
            return results
        except Exception as e:
            err_text = str(e)
            if "Ratelimit" in err_text or "202" in err_text:
                if attempt < _DDG_MAX_RETRIES:
                    logger.info(
                        "DDG rate-limited on attempt %d/%d, backing off %.1fs...",
                        attempt, _DDG_MAX_RETRIES, backoff,
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue
            logger.warning("DuckDuckGo search failed (attempt %d): %s", attempt, e)
            break
    return results
def _search_github(query: str, max_results: int = 3) -> list[dict]:
    """Search GitHub repositories."""
    settings = get_settings()
    results: list[dict] = []
    try:
        gh_q = requests.utils.quote(query)
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        r = requests.get(
            f"https://api.github.com/search/repositories?q={gh_q}&sort=stars&per_page={max_results}",
            headers=headers,
            timeout=10,
        )
        if r.status_code == 200:
            for repo in r.json().get("items", [])[:max_results]:
                results.append(
                    {
                        "title": repo.get("full_name", ""),
                        "snippet": (repo.get("description") or "")[:400],
                        "url": repo.get("html_url", ""),
                        "source": "github",
                        "stars": repo.get("stargazers_count", 0),
                        "date": datetime.now(timezone.utc).date().isoformat(),
                    }
                )
        else:
            logger.warning("GitHub search returned %d: %s", r.status_code, r.text[:200])
    except Exception as e:
        logger.warning("GitHub search failed: %s", e)
    return results
def _search_google_scrape(query: str, max_results: int = 5) -> list[dict]:
    """Lightweight fallback: scrape Google search results page."""
    results: list[dict] = []
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        r = requests.get(
            "https://www.google.com/search",
            params={"q": query, "num": max_results},
            headers=headers,
            timeout=10,
        )
        if r.status_code == 200:
            text = r.text
            url_pattern = re.compile(
                r'<a href="/url\?q=(https?://[^&"]+)[^"]*"[^>]*>(.*?)</a>',
                re.DOTALL,
            )
            snippet_pattern = re.compile(
                r'<span class="[^"]*"[^>]*>(.*?)</span>',
                re.DOTALL,
            )
            matches = url_pattern.findall(text)
            for url, title_html in matches[:max_results]:
                if "google.com" in url or "youtube.com" in url:
                    continue
                clean_title = re.sub(r"<[^>]+>", "", title_html).strip()
                if clean_title and url:
                    results.append(
                        {
                            "title": clean_title[:200],
                            "snippet": "",
                            "url": url,
                            "source": "google",
                            "date": datetime.now(timezone.utc).date().isoformat(),
                        }
                    )
        else:
            logger.warning("Google scrape returned %d", r.status_code)
    except Exception as e:
        logger.warning("Google scrape failed: %s", e)
    return results
def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search the web using DuckDuckGo (primary) and Google (fallback)."""
    settings = get_settings()
    if not settings.search_enabled:
        return []
    results: list[dict] = []
    ddg_results = _search_duckduckgo(query, max_results=max_results)
    results.extend(ddg_results)
    if not ddg_results:
        logger.info("DDG returned no results, trying Google scrape fallback...")
        google_results = _search_google_scrape(query, max_results=max_results)
        results.extend(google_results)
    return results
def format_search_context(results: list[dict]) -> str:
    if not results:
        return "No live search results available. State this in notes_and_limitations."
    lines = []
    for i, r in enumerate(results, 1):
        stars = f" ★{r['stars']}" if r.get("stars") else ""
        lines.append(
            f"[{i}] {r.get('title')} ({r.get('source')}){stars}\n"
            f"URL: {r.get('url')}\n"
            f"Snippet: {r.get('snippet')}\n"
            f"Retrieved: {r.get('date')}"
        )
    return "\n\n".join(lines)
def search_for_idea(idea: str) -> tuple[list[dict], str]:
    seen_urls: set[str] = set()
    merged: list[dict] = []
    gh_results = _search_github(idea[:80], max_results=5)
    for row in gh_results:
        url = row.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            merged.append(row)
    web_queries = [
        f"{idea[:80]} startup product",
        f"{idea[:80]} open source alternative",
        f"{idea[:80]} existing solutions",
    ]
    for i, q in enumerate(web_queries):
        if i > 0:
            time.sleep(1.5)
        for row in search_web(q, max_results=4):
            url = row.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(row)
    logger.info("Idea search returned %d total results", len(merged))
    return merged, format_search_context(merged)
