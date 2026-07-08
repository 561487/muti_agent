"""
Report Team — writes, visualizes, and edits the final competitive intelligence report.

Takes analysis output and produces a polished, professional report
in markdown format with optional charts.
"""

from langgraph.graph import StateGraph, START
from langgraph.prebuilt import create_react_agent

from contelix.config import ENABLE_DEBUG
from contelix.llm_factory import get_llm
from contelix.checkpoint.manager import get_checkpointer
from contelix.retry import AGENT_RETRY_POLICY
from contelix.agents.node_factory import make_agent_node
from contelix.state.schemas import ReportState
from contelix.state.supervisor_factory import make_supervisor_node
from contelix.tools.file_ops import (
    write_document,
    read_document,
    edit_document,
    create_outline,
)
from contelix.tools.visualization import execute_python, generate_comparison_chart

# ── Member definitions ─────────────────────────────────────────────────────
MEMBERS = ["outline_writer", "content_writer", "chart_generator", "editor"]

MEMBER_SCHEMA = {
    "outline_writer": {
        "prompt": (
            "You are a report structure expert. Your job is to:\n"
            "1. Read the analysis data provided.\n"
            "2. Create a logical, comprehensive outline for a competitive "
            "intelligence report.\n"
            "3. Save the outline using the create_outline tool.\n\n"
            "A good CI report structure includes:\n"
            "- Executive Summary\n"
            "- Company/Product Overview\n"
            "- Market Landscape\n"
            "- Competitive Analysis\n"
            "- SWOT Analysis\n"
            "- Trends & Outlook\n"
            "- Strategic Recommendations\n"
            "- Sources & References\n\n"
            "Save the outline as 'report_outline.txt'."
        ),
        "tools": [create_outline, read_document],
    },
    "content_writer": {
        "prompt": (
            "You are a professional competitive intelligence report writer. "
            "Your job is to:\n"
            "1. Read the analysis data and outline.\n"
            "2. Write a comprehensive, well-structured report in markdown.\n"
            "3. Save the full report using write_document.\n\n"
            "Writing guidelines:\n"
            "- Professional, objective tone suitable for business executives\n"
            "- Use markdown headers (##, ###) for structure\n"
            "- Include specific data points, facts, and quotes from research\n"
            "- Use markdown tables for competitive comparisons\n"
            "- Each section should be substantive (not just 1-2 sentences)\n"
            "- Include an executive summary at the top\n"
            "- End with actionable strategic recommendations\n\n"
            "Save as 'competitive_intelligence_report.md'."
        ),
        "tools": [write_document, read_document, edit_document],
    },
    "chart_generator": {
        "prompt": (
            "You are a data visualization specialist. Your job is to:\n"
            "1. Read the analysis data and report content.\n"
            "2. Create 1-2 relevant charts/visualizations using Python code.\n"
            "3. Save charts as PNG files.\n\n"
            "Chart ideas for competitive intelligence:\n"
            "- Feature comparison bar chart\n"
            "- Market share or positioning chart\n"
            "- Timeline of key events\n"
            "- Competitive landscape map\n\n"
            "Use matplotlib. Always use plt.savefig() to save. "
            "The output directory is already set up."
        ),
        "tools": [execute_python, generate_comparison_chart, read_document],
    },
    "editor": {
        "prompt": (
            "You are a senior editor for competitive intelligence reports. "
            "Your job is to:\n"
            "1. Read the complete report using read_document.\n"
            "2. Review it for quality: clarity, accuracy, completeness, professionalism.\n"
            "3. Use edit_document to fix issues, add missing context, or improve flow.\n"
            "4. Ensure the report is polished and ready for executive presentation.\n\n"
            "The report file is 'competitive_intelligence_report.md'."
        ),
        "tools": [read_document, edit_document],
    },
}


# ── Build agents ───────────────────────────────────────────────────────────
def _build_report_agents():
    agents = {}
    for name, cfg in MEMBER_SCHEMA.items():
        agents[name] = create_react_agent(
            get_llm(),
            tools=cfg["tools"],
            prompt=cfg["prompt"],
            debug=ENABLE_DEBUG,
        )
    return agents


_AGENTS = _build_report_agents()


# ── Build the Report Team graph ────────────────────────────────────────────

_supervisor_node = make_supervisor_node(
    get_llm(),
    MEMBERS,
    system_prompt=(
        f"You are the Report Team supervisor managing: {', '.join(MEMBERS)}.\n\n"
        "Your team's goal: Produce a polished, professional competitive "
        "intelligence report.\n\n"
        "Workflow (in order):\n"
        "1. Route to 'outline_writer' FIRST to create the report structure.\n"
        "2. Route to 'content_writer' to write the full report content.\n"
        "3. Route to 'chart_generator' to create relevant visualizations.\n"
        "4. Route to 'editor' for final review and polish.\n"
        "5. When the report is complete and polished, respond with 'FINISH'.\n\n"
        "IMPORTANT: Follow this order. Do not skip steps."
    ),
)


def build_report_graph() -> StateGraph:
    """Build and return the Report Team's StateGraph with checkpointing."""
    builder = StateGraph(ReportState)

    builder.add_node("supervisor", _supervisor_node, retry=AGENT_RETRY_POLICY)
    for name in MEMBERS:
        builder.add_node(
            name,
            make_agent_node(_AGENTS[name], name),
            retry=AGENT_RETRY_POLICY,
        )

    builder.add_edge(START, "supervisor")
    return builder.compile(checkpointer=get_checkpointer())
