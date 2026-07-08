"""
Top-Level Supervisor — orchestrates the Research, Analysis, and Report teams.

This is the "big boss" that routes the user's request through the three
stages of competitive intelligence: Research → Analysis → Report.
"""

from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START
from langgraph.types import Command

from contelix.config import (
    MAX_RECURSION_LIMIT,
    ENABLE_DEBUG,
    ENABLE_HUMAN_REVIEW,
)
from contelix.llm_factory import get_llm
from contelix.checkpoint.manager import get_checkpointer
from contelix.retry import AGENT_RETRY_POLICY
from contelix.state.schemas import OverallState
from contelix.state.supervisor_factory import make_supervisor_node

# ── LLM instance (lazy via factory) ──────────────────────────────────────────

def _get_llm():
    return get_llm()

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


def call_research_team(state: OverallState) -> Command[Literal["supervisor"]]:
    """
    Invoke the Research Team subgraph with the user's topic.
    The Research Team searches the web and scrapes content.
    """
    print("\n🔍 [Top Supervisor] Delegating to Research Team...")
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

    print("✅ [Top Supervisor] Research Team completed.")
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response["messages"][-1].content,
                    name="research_team",
                )
            ],
            "research_complete": True,
        },
        goto="supervisor",
    )


def call_analysis_team(state: OverallState) -> Command[Literal["supervisor"]]:
    """
    Invoke the Analysis Team subgraph with the research findings.
    Performs SWOT, trend, and competitive comparison analysis.
    """
    print("\n📊 [Top Supervisor] Delegating to Analysis Team...")
    graph = _get_analysis_graph()

    research_content = ""
    for msg in state.get("messages", []):
        if hasattr(msg, "name") and msg.name == "research_team":
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

    print("✅ [Top Supervisor] Analysis Team completed.")
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response["messages"][-1].content,
                    name="analysis_team",
                )
            ],
            "analysis_complete": True,
        },
        goto="supervisor",
    )


def call_report_team(state: OverallState) -> Command[Literal["supervisor"]]:
    """
    Invoke the Report Team subgraph with the analysis results.
    Writes, visualizes, and edits the final report.
    """
    print("\n📝 [Top Supervisor] Delegating to Report Team...")
    graph = _get_report_graph()

    analysis_content = ""
    for msg in state.get("messages", []):
        if hasattr(msg, "name") and msg.name == "analysis_team":
            analysis_content = msg.content
            break

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

    print("✅ [Top Supervisor] Report Team completed.")
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response["messages"][-1].content,
                    name="report_team",
                )
            ],
            "report_complete": True,
        },
        goto="supervisor",
    )


# ── Top supervisor node ────────────────────────────────────────────────────

TOP_MEMBERS = ["research_team", "analysis_team", "report_team"]

_top_supervisor = make_supervisor_node(
    _get_llm(),
    TOP_MEMBERS,
    system_prompt=(
        f"You are the Chief Competitive Intelligence Officer, managing three "
        f"specialized teams: research_team, analysis_team, report_team.\n\n"
        f"Your job is to route the user's research request through the correct "
        f"sequence, ensuring a complete competitive intelligence workflow.\n\n"
        f"IMPORTANT — You MUST follow this exact workflow order:\n"
        f"1. FIRST: Route to 'research_team' to gather web data.\n"
        f"2. SECOND: Route to 'analysis_team' to analyze the research.\n"
        f"3. THIRD: Route to 'report_team' to produce the final report.\n"
        f"4. When all three are done, respond with 'FINISH'.\n\n"
        f"DO NOT skip steps or route out of order. DO NOT route to the same "
        f"team twice unless there's a clear reason."
    ),
)


# ── Build the top-level graph ──────────────────────────────────────────────

def build_top_graph() -> StateGraph:
    """Build and return the top-level orchestration graph with checkpointing."""
    builder = StateGraph(OverallState)

    builder.add_node("supervisor", _top_supervisor, retry=AGENT_RETRY_POLICY)
    builder.add_node("research_team", call_research_team, retry=AGENT_RETRY_POLICY)
    builder.add_node("analysis_team", call_analysis_team, retry=AGENT_RETRY_POLICY)
    builder.add_node("report_team", call_report_team, retry=AGENT_RETRY_POLICY)

    builder.add_edge(START, "supervisor")

    return builder.compile(checkpointer=get_checkpointer())
