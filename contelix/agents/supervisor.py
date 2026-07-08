"""
Top-Level Orchestrator — chains Research → Analysis → Report teams.

Uses simple sequential edges instead of LLM-based routing since the
pipeline order is deterministic. Each team subgraph runs with its
own supervisor and returns results for the next stage.
"""

import structlog
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from contelix.config import MAX_RECURSION_LIMIT
from contelix.checkpoint.manager import get_checkpointer
from contelix.retry import AGENT_RETRY_POLICY
from contelix.state.schemas import OverallState

logger = structlog.get_logger(__name__)


# ── Team graph imports (lazy to avoid circular imports) ────────────────────


def _get_research_graph():
    from contelix.agents.research.supervisor import build_research_graph

    return build_research_graph()


def _get_analysis_graph():
    from contelix.agents.analysis.supervisor import build_analysis_graph

    return build_analysis_graph()


def _get_report_graph():
    from contelix.agents.reporting.supervisor import build_report_graph

    return build_report_graph()


# ── Team wrapper nodes ─────────────────────────────────────────────────────


def call_research_team(state: OverallState) -> dict:
    """Invoke the Research Team subgraph with the user's topic."""
    logger.info("delegating_to_team", team="research")
    graph = _get_research_graph()

    response = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        f"Research the following topic comprehensively: {state['topic']}\n\n"
                        "Search for news, competitor information, market data, product "
                        "details, financial information, and industry trends. Gather as "
                        "much relevant data as possible. When done, compile a detailed "
                        "research brief."
                    )
                )
            ]
        },
        {"recursion_limit": MAX_RECURSION_LIMIT},
    )

    logger.info("team_completed", team="research")
    return {
        "messages": [
            HumanMessage(
                content=response["messages"][-1].content,
                name="research_team",
            )
        ],
    }


def call_analysis_team(state: OverallState) -> dict:
    """Invoke the Analysis Team subgraph with research findings."""
    logger.info("delegating_to_team", team="analysis")
    graph = _get_analysis_graph()

    research_content = ""
    for msg in state.get("messages", []):
        if getattr(msg, "name", None) == "research_team":
            research_content = msg.content
            break

    response = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        f"Analyze the following research data on '{state['topic']}':\n\n"
                        f"{research_content}\n\n"
                        "Perform: 1) SWOT analysis, 2) Market trend analysis, "
                        "3) Competitive comparison. Be thorough and evidence-based."
                    )
                )
            ]
        },
        {"recursion_limit": MAX_RECURSION_LIMIT},
    )

    logger.info("team_completed", team="analysis")
    return {
        "messages": [
            HumanMessage(
                content=response["messages"][-1].content,
                name="analysis_team",
            )
        ],
    }


def call_report_team(state: OverallState) -> dict:
    """Invoke the Report Team subgraph with analysis results."""
    logger.info("delegating_to_team", team="report")
    graph = _get_report_graph()

    analysis_content = ""
    for msg in state.get("messages", []):
        if getattr(msg, "name", None) == "analysis_team":
            analysis_content = msg.content
            break

    try:
        response = graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=(
                            f"Create a professional competitive intelligence report "
                            f"on the topic: '{state['topic']}'.\n\n"
                            f"Analysis data to use:\n{analysis_content}\n\n"
                            "Create: 1) Report outline, 2) Full report content in markdown, "
                            "3) Relevant charts/visualizations, 4) Final editing pass. "
                            "Save the final report as 'competitive_intelligence_report.md'."
                        )
                    )
                ]
            },
            {"recursion_limit": MAX_RECURSION_LIMIT},
        )
    except Exception:
        logger.error("team_failed", team="report", exc_info=True)
        return {
            "messages": [
                HumanMessage(
                    content="[report_team] Failed to generate report. See logs for details.",
                    name="report_team",
                )
            ],
        }

    logger.info("team_completed", team="report")
    return {
        "messages": [
            HumanMessage(
                content=response["messages"][-1].content,
                name="report_team",
            )
        ],
    }


# ── Build the top-level graph ──────────────────────────────────────────────


def build_top_graph() -> StateGraph:
    """Build the top-level orchestration graph as a sequential pipeline."""
    builder = StateGraph(OverallState)

    builder.add_node("research_team", call_research_team, retry=AGENT_RETRY_POLICY)
    builder.add_node("analysis_team", call_analysis_team, retry=AGENT_RETRY_POLICY)
    builder.add_node("report_team", call_report_team, retry=AGENT_RETRY_POLICY)

    # Simple sequential pipeline — no LLM routing needed
    builder.add_edge(START, "research_team")
    builder.add_edge("research_team", "analysis_team")
    builder.add_edge("analysis_team", "report_team")
    builder.add_edge("report_team", END)

    return builder.compile(checkpointer=get_checkpointer())
