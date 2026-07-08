"""
Research Team — searches the web and scrapes detailed content.

This team compiles a comprehensive research brief from multiple
web sources on a given competitive intelligence topic.
"""

from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from contelix.config import ENABLE_DEBUG
from contelix.llm_factory import get_llm
from contelix.checkpoint.manager import get_checkpointer
from contelix.retry import AGENT_RETRY_POLICY
from contelix.agents.node_factory import make_agent_node
from contelix.state.schemas import ResearchState
from contelix.state.supervisor_factory import make_supervisor_node
from contelix.tools.search import competitive_search, search_news
from contelix.tools.scraping import scrape_webpages

# ── LLM instance (lazy via factory) ───────────────────────────────────────

def _get_llm():
    return get_llm()

# ── Member definitions ─────────────────────────────────────────────────────
MEMBERS = ["search_agent", "scraper_agent"]
MEMBER_SCHEMA = {
    "search_agent": {
        "prompt": (
            "You are a competitive intelligence researcher. "
            "Search the web for information about companies, products, markets, "
            "and competitors. Use multiple search queries to get comprehensive "
            "coverage. When you have good results, return a structured summary."
        ),
        "tools": [competitive_search, search_news],
    },
    "scraper_agent": {
        "prompt": (
            "You are a content extraction specialist. "
            "Take URLs from the search results and scrape them for detailed "
            "information. Extract key facts, statistics, quotes, and data points. "
            "Compile everything into a well-organized research brief."
        ),
        "tools": [scrape_webpages],
    },
}


# ── Build agents ───────────────────────────────────────────────────────────
def _build_research_agents():
    """Create the search and scraper react agents."""
    agents = {}
    for name, cfg in MEMBER_SCHEMA.items():
        agents[name] = create_react_agent(
            _get_llm(),
            tools=cfg["tools"],
            prompt=cfg["prompt"],
            debug=ENABLE_DEBUG,
        )
    return agents


_AGENTS = _build_research_agents()


# ── Build the Research Team graph ──────────────────────────────────────────

_supervisor_node = make_supervisor_node(
    _get_llm(),
    MEMBERS,
    system_prompt=(
        f"You are the Research Team supervisor managing: {', '.join(MEMBERS)}.\n\n"
        "Your team's goal: Gather comprehensive information from the web about "
        "the user's research topic.\n\n"
        "Workflow:\n"
        "1. First, route to 'search_agent' to find relevant web pages and news.\n"
        "2. Then, route to 'scraper_agent' to extract detailed content from "
        "   the most promising URLs found by search_agent.\n"
        "3. You may loop back to search_agent for more targeted searches if needed.\n"
        "4. When you have sufficient research data, respond with 'FINISH'.\n\n"
        "Output should be a comprehensive research brief with key findings, "
        "facts, and data points about the topic."
    ),
)


def build_research_graph() -> StateGraph:
    """Build and return the Research Team's StateGraph with checkpointing."""
    builder = StateGraph(ResearchState)

    builder.add_node("supervisor", _supervisor_node, retry=AGENT_RETRY_POLICY)
    for name in MEMBERS:
        builder.add_node(
            name,
            make_agent_node(_AGENTS[name], name),
            retry=AGENT_RETRY_POLICY,
        )

    builder.add_edge(START, "supervisor")
    return builder.compile(checkpointer=get_checkpointer())
