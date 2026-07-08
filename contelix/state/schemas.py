"""
State schemas for the Contelix multi-agent system.

Each team has its own state schema, plus there is an overall
state that flows through the top-level supervisor.
"""

from typing import Annotated, List, Optional
from typing_extensions import TypedDict

from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


# ── Research Team State ────────────────────────────────────────────────────

class ResearchState(MessagesState):
    """State for the Research Team (search + scrape agents)."""

    research_topic: str
    """The topic/query being researched."""

    search_results: List[dict]
    """Collected search results with urls and snippets."""

    scraped_content: str
    """Raw content scraped from web pages."""

    research_summary: str
    """Synthesized summary of all research findings."""


# ── Analysis Team State ────────────────────────────────────────────────────

class AnalysisState(MessagesState):
    """State for the Analysis Team (SWOT, trend, comparison agents)."""

    research_data: str
    """Research data to analyze (from Research Team output)."""

    swot_result: str
    """SWOT analysis output (Strengths, Weaknesses, Opportunities, Threats)."""

    trend_result: str
    """Market/industry trend analysis output."""

    comparison_result: str
    """Competitive comparison analysis output."""


# ── Report Team State ──────────────────────────────────────────────────────

class ReportState(MessagesState):
    """State for the Report Team (writer, chart, editor agents)."""

    analysis_data: str
    """Analysis data to use in the report (from Analysis Team output)."""

    topic: str
    """The original research topic for the report title."""

    report_outline: List[str]
    """Report section outline."""

    report_content: str
    """Current draft of the report content."""

    charts: List[str]
    """Paths to generated chart files."""

    final_report_path: str
    """Path to the final saved report file."""


# ── Overall State (Top-Level Supervisor) ───────────────────────────────────

class OverallState(MessagesState):
    """Top-level state flowing through the main supervisor."""

    topic: str
    """The user's research topic."""

    next_team: str
    """Next team to route to: 'research_team', 'analysis_team', 'report_team', or 'FINISH'."""

    research_complete: bool
    """Whether the research phase is done."""

    analysis_complete: bool
    """Whether the analysis phase is done."""

    report_complete: bool
    """Whether the report is done."""

    output_dir: str
    """Output directory for generated files."""
