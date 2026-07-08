"""
State schemas for the Contelix multi-agent system.

Each team extends MessagesState (which provides the ``messages`` field
used for agent communication). Additional typed fields can be added as
the data flow becomes more structured.
"""

from langgraph.graph import MessagesState


# ── Research Team State ────────────────────────────────────────────────────


class ResearchState(MessagesState):
    """State for the Research Team (search + scrape agents)."""

    research_topic: str = ""
    """The topic/query being researched."""


# ── Analysis Team State ────────────────────────────────────────────────────


class AnalysisState(MessagesState):
    """State for the Analysis Team (SWOT, trend, comparison agents)."""

    research_data: str = ""
    """Research data to analyze (from Research Team output)."""


# ── Report Team State ──────────────────────────────────────────────────────


class ReportState(MessagesState):
    """State for the Report Team (outline, write, chart, edit agents)."""

    analysis_data: str = ""
    """Analysis data to use in the report (from Analysis Team output)."""

    topic: str = ""
    """The original research topic for the report title."""


# ── Overall State (Top-Level Orchestrator) ─────────────────────────────────


class OverallState(MessagesState):
    """Top-level state flowing through the Research → Analysis → Report pipeline."""

    topic: str = ""
    """The user's research topic."""
