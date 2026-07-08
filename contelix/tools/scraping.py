"""
Web scraping tools for extracting detailed content from web pages.
"""

from typing import List

from langchain_community.document_loaders import WebBaseLoader
from langchain_core.tools import tool


@tool
def scrape_webpages(urls: List[str]) -> str:
    """
    Scrape and extract content from one or more web pages.

    Use this tool after search to get detailed information from
    specific URLs. This extracts the full text content of web pages.

    Args:
        urls: List of URLs to scrape. Provide 1-5 URLs at a time.

    Returns:
        Extracted text content from all URLs, separated by document markers.
    """
    if not urls:
        return "No URLs provided."

    # Limit to 5 URLs per call to avoid overwhelming the system
    urls = urls[:5]

    try:
        loader = WebBaseLoader(
            urls,
            header_template={"User-Agent": "Contelix/0.1 Research Agent"},
        )
        docs = loader.load()

        if not docs:
            return "No content could be extracted from the provided URLs."

        output_parts = []
        for doc in docs:
            title = doc.metadata.get("title", "Untitled")
            source = doc.metadata.get("source", "")
            content = doc.page_content[:8000]  # Truncate very long pages
            output_parts.append(
                f'<Document title="{title}" source="{source}">\n'
                f"{content}\n"
                f"</Document>"
            )

        return "\n\n---\n\n".join(output_parts)

    except Exception as e:
        return f"Error scraping webpages: {str(e)}"


@tool
def extract_key_info(
    url: str,
    focus_areas: str = "products, competitors, market position, strategy",
) -> str:
    """
    Scrape a single URL and extract key competitive intelligence.

    Unlike scrape_webpages which returns raw content, this tool
    scrapes a page and asks the LLM to extract specific types of
    business intelligence from it.

    Args:
        url: The URL to scrape and analyze.
        focus_areas: Comma-separated list of what to look for
                     (e.g., 'products, pricing, leadership, funding').

    Returns:
        Extracted key information organized by focus area.
    """
    try:
        loader = WebBaseLoader(
            [url],
            header_template={"User-Agent": "Contelix/0.1 Research Agent"},
        )
        docs = loader.load()

        if not docs:
            return f"No content could be extracted from {url}"

        content = docs[0].page_content[:10000]
        title = docs[0].metadata.get("title", "Untitled")

        return (
            f"--- Content from: {title} ({url}) ---\n"
            f"Focus areas: {focus_areas}\n\n"
            f"{content}\n"
            f"--- End of content ---\n\n"
            f"Please extract and organize key information related to: {focus_areas}"
        )

    except Exception as e:
        return f"Error extracting info from {url}: {str(e)}"
