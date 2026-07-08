"""
Analysis Team — analyzes research data to produce competitive insights.

Performs SWOT analysis, trend identification, and competitive comparison
on the research data gathered by the Research Team.
"""

from langgraph.graph import StateGraph, START
from langgraph.prebuilt import create_react_agent

from contelix.config import ENABLE_DEBUG
from contelix.llm_factory import get_llm
from contelix.checkpoint.manager import get_checkpointer
from contelix.retry import AGENT_RETRY_POLICY
from contelix.agents.node_factory import make_agent_node
from contelix.state.schemas import AnalysisState
from contelix.state.supervisor_factory import make_supervisor_node
from contelix.tools.file_ops import write_document

# ── Member definitions ─────────────────────────────────────────────────────
MEMBERS = ["swot_analyst", "trend_analyst", "comparison_analyst"]

MEMBER_SCHEMA = {
    "swot_analyst": {
        "prompt": (
            "You are a SWOT analysis expert. Your job is to analyze a company, "
            "product, or market and identify:\n"
            "- **Strengths**: Internal advantages, unique capabilities, resources\n"
            "- **Weaknesses**: Internal limitations, gaps, vulnerabilities\n"
            "- **Opportunities**: External factors to exploit, market gaps, trends\n"
            "- **Threats**: External risks, competitors, regulatory challenges\n\n"
            "Be specific, evidence-based, and actionable. Use the research data "
            "provided to you. Format your analysis in clear markdown sections."
        ),
        "tools": [write_document],
    },
    "trend_analyst": {
        "prompt": (
            "You are a market trends analyst. Your job is to identify and analyze:\n"
            "- Key industry trends and their trajectory\n"
            "- Technology shifts and innovation patterns\n"
            "- Consumer/customer behavior changes\n"
            "- Regulatory and policy trends\n"
            "- Market growth/shrinkage patterns\n\n"
            "Use the research data to support your analysis. Provide specific "
            "examples and data points. Format in clear markdown with bullet points."
        ),
        "tools": [write_document],
    },
    "comparison_analyst": {
        "prompt": (
            "You are a competitive comparison analyst. Your job is to:\n"
            "- Identify key competitors and their positions\n"
            "- Compare features, pricing, market share, strategies\n"
            "- Create structured comparison tables (in markdown)\n"
            "- Highlight competitive advantages and disadvantages\n"
            "- Provide strategic recommendations\n\n"
            "Use the research data to make evidence-based comparisons. "
            "Format in clear markdown with comparison tables where helpful."
        ),
        "tools": [write_document],
    },
}


# ── Build agents ───────────────────────────────────────────────────────────
def _build_analysis_agents():
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
        _AGENTS = _build_analysis_agents()
    return _AGENTS


# ── Build the Analysis Team graph ──────────────────────────────────────────

_supervisor_node = make_supervisor_node(
    get_llm(),
    MEMBERS,
    system_prompt=(
        f"You are the Analysis Team supervisor managing: {', '.join(MEMBERS)}.\n\n"
        "Your team's goal: Analyze research data to produce actionable "
        "competitive intelligence insights.\n\n"
        "Workflow:\n"
        "1. Route to 'swot_analyst' for SWOT analysis.\n"
        "2. Route to 'trend_analyst' for market trend analysis.\n"
        "3. Route to 'comparison_analyst' for competitive comparison.\n"
        "4. These can run in any order. When all three analyses are complete, "
        "respond with 'FINISH'.\n\n"
        "Each analyst will save their output. The final combined analysis "
        "will be used by the Report Team."
    ),
)


def build_analysis_graph() -> StateGraph:
    """Build and return the Analysis Team's StateGraph with checkpointing."""
    builder = StateGraph(AnalysisState)

    builder.add_node("supervisor", _supervisor_node, retry=AGENT_RETRY_POLICY)
    for name in MEMBERS:
        builder.add_node(
            name,
            make_agent_node(_get_agents()[name], name),
            retry=AGENT_RETRY_POLICY,
        )

    builder.add_edge(START, "supervisor")
    return builder.compile(checkpointer=get_checkpointer())
