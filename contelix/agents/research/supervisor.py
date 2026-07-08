"""
Research Team — searches the web and scrapes detailed content.

This team compiles a comprehensive research brief from multiple
web sources on a given competitive intelligence topic.
"""

from langgraph.graph import StateGraph, START
from langgraph.prebuilt import create_react_agent

from contelix.config import ENABLE_DEBUG
from contelix.llm_factory import get_llm
from contelix.retry import AGENT_RETRY_POLICY
from contelix.agents.node_factory import make_agent_node
from contelix.state.schemas import ResearchState
from contelix.state.supervisor_factory import make_supervisor_node
from contelix.tools.search import competitive_search, search_news
from contelix.tools.scraping import scrape_webpages

# ── Member definitions ─────────────────────────────────────────────────────
MEMBERS = ["search_agent", "scraper_agent"]
MEMBER_SCHEMA = {
    "search_agent": {
        "prompt": (
            "你是一名竞争情报研究员。请围绕目标公司、产品或市场进行多角度搜索，"
            "使用不同关键词组合以获得全面覆盖。获得充分结果后，整理为结构化的研究摘要。"
            "请用中文输出。"
        ),
        "tools": [competitive_search, search_news],
    },
    "scraper_agent": {
        "prompt": (
            "你是一名内容提取专家。请从搜索结果中的 URL 抓取详细页面内容，"
            "提取关键事实、数据、引用和观点。将所有信息整理成条理清晰的研究简报。"
            "请用中文输出。"
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
            get_llm(),
            tools=cfg["tools"],
            prompt=cfg["prompt"],
            debug=ENABLE_DEBUG,
        )
    return agents


_AGENTS = None


def _get_agents():
    """Lazy-initialize and cache agent instances."""
    global _AGENTS
    if _AGENTS is None:
        _AGENTS = _build_research_agents()
    return _AGENTS


# ── Build the Research Team graph ──────────────────────────────────────────

_supervisor_node = make_supervisor_node(
    get_llm(),
    MEMBERS,
    system_prompt=(
        f"你是研究团队的 Supervisor，管理以下成员: {', '.join(MEMBERS)}。\n\n"
        "团队目标: 从互联网收集关于用户研究话题的全面信息。\n\n"
        "工作流程:\n"
        "1. 首先将任务路由给 'search_agent' 搜索相关网页和新闻。\n"
        "2. 然后将搜索到的优质 URL 路由给 'scraper_agent' 提取详细内容。\n"
        "3. 如有需要，可以回到 search_agent 进行更精准的补充搜索。\n"
        "4. 获得充分的研究数据后，回复 'FINISH' 结束。\n\n"
        "请用中文输出。"
    ),
)


def build_research_graph() -> StateGraph:
    """Build and return the Research Team's StateGraph with checkpointing."""
    builder = StateGraph(ResearchState)

    builder.add_node("supervisor", _supervisor_node, retry=AGENT_RETRY_POLICY)
    for name in MEMBERS:
        builder.add_node(
            name,
            make_agent_node(_get_agents()[name], name),
            retry=AGENT_RETRY_POLICY,
        )

    builder.add_edge(START, "supervisor")
    return builder.compile()
