"""
Report Team — writes, visualizes, and edits the final competitive intelligence report.

Takes analysis output and produces a polished, professional report
in markdown format with optional charts.
"""

from langgraph.graph import StateGraph, START
from langgraph.prebuilt import create_react_agent

from contelix.config import ENABLE_DEBUG
from contelix.llm_factory import get_llm
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
            "你是一名报告结构专家。请:\n"
            "1. 阅读提供的分析数据。\n"
            "2. 为竞争情报报告创建逻辑清晰、内容全面的结构大纲。\n"
            "3. 使用 create_outline 工具保存大纲。\n\n"
            "一份好的 CI 报告应包含:\n"
            "- 执行摘要\n"
            "- 公司/产品概览\n"
            "- 市场格局\n"
            "- 竞争分析\n"
            "- SWOT 分析\n"
            "- 趋势与展望\n"
            "- 战略建议\n"
            "- 来源与参考\n\n"
            "保存为 'report_outline.txt'。请用中文输出。"
        ),
        "tools": [create_outline, read_document],
    },
    "content_writer": {
        "prompt": (
            "你是一名专业的竞争情报报告撰写人。请:\n"
            "1. 阅读分析数据和大纲。\n"
            "2. 撰写一份全面、结构清晰的 Markdown 格式报告。\n"
            "3. 使用 write_document 保存完整报告。\n\n"
            "撰写要求:\n"
            "- 面向企业高管的专业、客观语调\n"
            "- 使用 Markdown 标题（##、###）组织结构\n"
            "- 引用具体数据、事实和来源\n"
            "- 使用 Markdown 表格进行对比分析\n"
            "- 每节内容充实（不要只有一两句话）\n"
            "- 顶部包含执行摘要\n"
            "- 结尾提供可落地的战略建议\n\n"
            "保存为 'competitive_intelligence_report.md'。请用中文输出。"
        ),
        "tools": [write_document, read_document, edit_document],
    },
    "chart_generator": {
        "prompt": (
            "你是一名数据可视化专家。请:\n"
            "1. 阅读分析数据和报告内容。\n"
            "2. 用 Python 代码创建 1-2 个相关图表。\n"
            "3. 将图表保存为 PNG 文件。\n\n"
            "竞争情报常用图表:\n"
            "- 功能对比柱状图\n"
            "- 市场份额或定位图\n"
            "- 关键事件时间线\n"
            "- 竞争格局图\n\n"
            "使用 matplotlib，始终用 plt.savefig() 保存。请用中文输出。"
        ),
        "tools": [execute_python, generate_comparison_chart, read_document],
    },
    "editor": {
        "prompt": (
            "你是一名竞争情报报告的高级编辑。请:\n"
            "1. 使用 read_document 阅读完整报告。\n"
            "2. 审核质量: 清晰度、准确性、完整性、专业性。\n"
            "3. 使用 edit_document 修复问题、补充遗漏、优化行文。\n"
            "4. 确保报告达到可向管理层呈报的标准。\n\n"
            "报告文件为 'competitive_intelligence_report.md'。请用中文输出。"
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


_AGENTS = None


def _get_agents():
    """Lazy-initialize and cache agent instances."""
    global _AGENTS
    if _AGENTS is None:
        _AGENTS = _build_report_agents()
    return _AGENTS


# ── Build the Report Team graph ────────────────────────────────────────────

_supervisor_node = make_supervisor_node(
    get_llm(),
    MEMBERS,
    system_prompt=(
        f"你是报告团队的 Supervisor，管理成员: {', '.join(MEMBERS)}。\n\n"
        "团队目标: 产出打磨完善的、专业的竞争情报报告。\n\n"
        "工作流程（严格按顺序）:\n"
        "1. 首先路由给 'outline_writer' 创建报告结构大纲。\n"
        "2. 然后路由给 'content_writer' 撰写完整报告内容。\n"
        "3. 接着路由给 'chart_generator' 创建可视化图表。\n"
        "4. 最后路由给 'editor' 进行最终审核润色。\n"
        "5. 报告完成后回复 'FINISH'。\n\n"
        "重要: 严格按此顺序，不要跳过任何步骤。"
    ),
)


def build_report_graph() -> StateGraph:
    """Build and return the Report Team's StateGraph with checkpointing."""
    builder = StateGraph(ReportState)

    builder.add_node("supervisor", _supervisor_node, retry=AGENT_RETRY_POLICY)
    for name in MEMBERS:
        builder.add_node(
            name,
            make_agent_node(_get_agents()[name], name),
            retry=AGENT_RETRY_POLICY,
        )

    builder.add_edge(START, "supervisor")
    return builder.compile()
