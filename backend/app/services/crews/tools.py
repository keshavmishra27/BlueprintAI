from crewai.tools import tool
from backend.app.services.search_service import format_search_context, search_web
@tool("Web Search")
def web_search_tool(query: str) -> str:
    """Search DuckDuckGo and GitHub for products, repos, and prior art. Input: search query string."""
    results = search_web(query, max_results=6)
    return format_search_context(results)
