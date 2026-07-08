"""
Analysis Team — analyzes research data to produce competitive insights.

Performs SWOT analysis, trend identification, and competitive comparison
on the research data gathered by the Research Team.
"""

from langgraph.graph import StateGraph, START
from langgraph.prebuilt import create_react_agent

from contelix.config import ENABLE_DEBUG
from contelix.llm_factory import get_llm
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
            "你是一名 SWOT 分析专家。请分析目标公司、产品或市场，识别:\n"
            "- **优势 (Strengths)**: 内部优势、独特能力、核心资源\n"
            "- **劣势 (Weaknesses)**: 内部局限、短板、脆弱环节\n"
            "- **机会 (Opportunities)**: 外部可利用因素、市场空白、趋势红利\n"
            "- **威胁 (Threats)**: 外部风险、竞争对手、监管挑战\n\n"
            "分析要具体、有据、可落地。基于提供的研究数据展开，"
            "用清晰的 Markdown 格式组织内容。请用中文输出。"
        ),
        "tools": [write_document],
    },
    "trend_analyst": {
        "prompt": (
            "你是一名市场趋势分析师。请识别并分析:\n"
            "- 关键行业趋势及其发展轨迹\n"
            "- 技术变革和创新模式\n"
            "- 消费者/用户行为变化\n"
            "- 监管和政策趋势\n"
            "- 市场增长/萎缩模式\n\n"
            "基于研究数据支撑分析，提供具体案例和数据点。"
            "用清晰的 Markdown 格式和要点组织内容。请用中文输出。"
        ),
        "tools": [write_document],
    },
    "comparison_analyst": {
        "prompt": (
            "你是一名竞品对比分析师。请完成:\n"
            "- 识别主要竞争对手及其市场定位\n"
            "- 对比产品功能、定价、市场份额、战略\n"
            "- 创建结构化的对比表格（Markdown 格式）\n"
            "- 突出竞争优势和劣势\n"
            "- 提供战略性建议\n\n"
            "基于研究数据进行客观对比，在合适的地方使用对比表格。"
            "请用中文输出。"
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
        f"你是分析团队的 Supervisor，管理成员: {', '.join(MEMBERS)}。\n\n"
        "团队目标: 分析研究数据，产出可落地的竞争情报洞察。\n\n"
        "工作流程:\n"
        "1. 将任务路由给 'swot_analyst' 进行 SWOT 分析。\n"
        "2. 将任务路由给 'trend_analyst' 进行市场趋势分析。\n"
        "3. 将任务路由给 'comparison_analyst' 进行竞品对比。\n"
        "4. 三者可任意顺序执行。全部完成后回复 'FINISH'。\n\n"
        "每位分析师会保存各自的分析结果，最终合并输出将交给报告团队。"
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
    return builder.compile()
