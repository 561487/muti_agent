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
                        f"请全面研究以下话题：{state['topic']}\n\n"
                        "搜索相关新闻、竞争对手信息、市场数据、产品细节、财务信息和行业趋势。"
                        "尽可能收集多的相关数据。完成后，整理一份详细的研究简报。"
                        "请用中文输出。"
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
                        f"请分析以下关于'{state['topic']}'的研究数据：\n\n"
                        f"{research_content}\n\n"
                        "请完成：1) SWOT 分析，2) 市场趋势分析，"
                        "3) 竞争对手对比分析。务必深入、有理有据。"
                        "请用中文输出。"
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
                            f"请基于分析数据撰写专业竞争情报报告，"
                            f"主题: '{state['topic']}'。\n\n"
                            f"分析数据:\n{analysis_content}\n\n"
                            "请完成: 1) 报告大纲，2) 完整报告(Markdown)，"
                            "3) 图表可视化，4) 最终编辑润色。"
                            "保存为 'competitive_intelligence_report.md'。"
                            "请用中文输出。"
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
                    content="[report_team] 报告生成失败，请查看日志了解详情。",
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
