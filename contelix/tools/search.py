"""
Web search tools for competitive intelligence gathering.

Supports both BochaAI and Tavily search backends.
"""

import json
from typing import List, Optional

import requests
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

from contelix.config import BOCHA_API_KEY, TAVILY_API_KEY


def _bocha_search(query: str, count: int = 10) -> List[dict]:
    """
    Perform a web search using the BochaAI API.

    Args:
        query: Search query string.
        count: Number of results to return (max 10).

    Returns:
        List of search result dicts with 'title', 'url', 'snippet' keys.
    """
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "summary": True,
        "count": min(count, 10),
        "page": 1,
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code != 200:
        return [
            {
                "title": "Search Error",
                "url": "",
                "snippet": f"Search failed: HTTP {response.status_code} — {response.text[:200]}",
            }
        ]

    results = response.json()
    output = []
    for item in results.get("data", {}).get("webPages", {}).get("value", []):
        output.append({
            "title": item.get("name", ""),
            "url": item.get("url", ""),
            "snippet": item.get("snippet", ""),
        })
    return output


@tool
def competitive_search(
    query: str,
    num_results: int = 8,
) -> str:
    """
    Search the web for competitive intelligence information.

    Use this tool to find information about companies, products, markets,
    industry trends, competitors, and business news. This is the primary
    research tool for gathering competitive intelligence data.

    Args:
        query: The search query. Be specific — include company names,
               product categories, or industry terms.
        num_results: Number of search results (1-10, default 8).

    Returns:
        Formatted search results with titles, URLs, and snippets.
    """
    if TAVILY_API_KEY:
        try:
            tavily = TavilySearchResults(max_results=min(num_results, 10))
            result = tavily.invoke({"query": query})
            if isinstance(result, list):
                lines = []
                for i, r in enumerate(result, 1):
                    content = r.get("content", "") if isinstance(r, dict) else str(r)
                    url = r.get("url", "") if isinstance(r, dict) else ""
                    lines.append(f"{i}. {content}\n   URL: {url}")
                return "\n\n".join(lines)
        except Exception:
            print("[search] Tavily search unavailable, falling back to BochaAI")

    # Fall back to BochaAI
    if not BOCHA_API_KEY:
        return "ERROR: No search API key configured. Set BOCHA_API_KEY or TAVILY_API_KEY."

    results = _bocha_search(query, count=num_results)
    if not results:
        return "No search results found. Try a different query."

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"{i}. **{r['title']}**\n"
            f"   {r['snippet']}\n"
            f"   URL: {r['url']}"
        )
    return "\n\n".join(lines)


@tool
def search_news(
    query: str,
    num_results: int = 5,
) -> str:
    """
    Search specifically for recent news articles about a topic.

    Use this to find the latest news, announcements, and press coverage
    about competitors, products, or industry developments.

    Args:
        query: The search query focused on news.
        num_results: Number of news results (1-10, default 5).

    Returns:
        Formatted news results with titles, URLs, and snippets.
    """
    return competitive_search.invoke({
        "query": f"{query} latest news",
        "num_results": num_results,
    })
