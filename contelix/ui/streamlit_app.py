"""
Contelix Streamlit Web UI — 竞争情报交互式研究界面.

启动方式:
    streamlit run contelix/ui/streamlit_app.py
    或: contelix run-ui
"""

import sys
import uuid
from pathlib import Path

import bleach
import streamlit as st

# HTML 标签白名单（XSS 防护）
_ALLOWED_TAGS = [
    "b", "i", "strong", "em", "code", "pre",
    "div", "span", "br", "p", "ul", "ol", "li", "a",
    "h1", "h2", "h3", "h4", "table", "thead", "tbody", "tr", "th", "td",
]
_ALLOWED_ATTRS = {
    "div": ["class"],
    "span": ["class"],
    "a": ["href", "title"],
}

# 确保项目根目录在路径中
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from contelix.config import (
    validate_config,
    OUTPUT_DIR,
    MAX_RECURSION_LIMIT,
)
from contelix.agents.supervisor import build_top_graph

# ── 页面配置 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Contelix — 竞争情报 AI 平台",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 样式 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.agent-msg {
    padding: 8px 12px;
    margin: 4px 0;
    border-radius: 8px;
    font-size: 0.9em;
}
.agent-research { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
.agent-analysis { background-color: #f3e5f5; border-left: 4px solid #9c27b0; }
.agent-report { background-color: #e8f5e9; border-left: 4px solid #4caf50; }
</style>
""", unsafe_allow_html=True)

# ── 会话状态 ────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "running" not in st.session_state:
    st.session_state.running = False
if "graph" not in st.session_state:
    st.session_state.graph = None

# ── 侧边栏 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 Contelix")
    st.caption("AI 竞争情报自动化平台")

    st.divider()

    # API 状态
    if validate_config():
        st.success("✅ API 已配置")
    else:
        st.error("⚠️ API Key 缺失")
        st.caption("请配置环境变量或创建 .env 文件")

    st.divider()

    # 设置
    st.subheader("⚙️ 设置")
    recursion = st.slider("最大步数", 50, 300, MAX_RECURSION_LIMIT, step=10)
    show_details = st.checkbox("显示 Agent 详情", value=True)

    st.divider()

    # 关于
    st.subheader("ℹ️ 关于")
    st.markdown("""
    **Contelix** 使用多智能体 AI 系统完成:
    1. 🔍 **搜索** — 全网搜索资料
    2. 📊 **分析** — SWOT / 趋势 / 竞品对比
    3. 📝 **报告** — 生成专业报告

    基于 LangGraph + Qwen2.5 构建
    """)

    st.divider()

    st.caption(f"输出目录: `{OUTPUT_DIR}`")

# ── 主界面 ──────────────────────────────────────────────────────────────────
st.title("🔍 竞争情报研究")
st.caption("输入一个公司、产品或行业话题，AI 智能体团队将自动搜索、分析并生成报告。")

# 输入区
col1, col2 = st.columns([5, 1])
with col1:
    topic = st.text_input(
        "研究话题",
        placeholder="例如：特斯拉在全球电动车市场的竞争地位",
        label_visibility="collapsed",
        key="topic_input",
    )
with col2:
    run_button = st.button("🚀 开始研究", type="primary", use_container_width=True)

# 示例话题
with st.expander("💡 示例话题"):
    st.markdown("""
    - 特斯拉在全球电动车市场的竞争地位
    - OpenAI、Google、Anthropic AI 战略对比
    - 云计算市场：AWS vs 阿里云 vs 华为云
    - Apple Vision Pro 竞争格局与市场影响
    - 支付平台对比：支付宝 vs 微信支付 vs Stripe
    """)

# ── 执行研究 ────────────────────────────────────────────────────────────────
if run_button and topic:
    if not validate_config():
        st.error("⚠️ API Key 未配置，请设置 CONTELIX_MODEL_API_KEY 和搜索 Key。")
        st.stop()

    st.session_state.running = True
    st.session_state.messages = []

    status_area = st.empty()
    progress_bar = st.progress(0, text="正在启动...")
    log_container = st.container()

    with log_container:
        st.subheader("📋 Agent 活动日志")

    with st.spinner("正在构建 Agent 管线..."):
        graph = build_top_graph()

    phase_map = {
        "research_team": ("🔍", "搜索中（网络搜索 + 网页抓取）..."),
        "analysis_team": ("📊", "分析中（SWOT + 趋势 + 竞品对比）..."),
        "report_team": ("📝", "写报告中（大纲 + 内容 + 图表 + 编辑）..."),
    }

    event_index = 0
    total_phases = 4

    try:
        for event in graph.stream(
            {"topic": topic, "messages": [{"role": "user", "content": topic}]},
            {
                "configurable": {"thread_id": str(uuid.uuid4())[:8]},
                "recursion_limit": recursion,
            },
            subgraphs=True,
        ):
            if isinstance(event, tuple) and len(event) == 2:
                _, event = event

            event_index += 1
            progress = min(event_index / (total_phases * 3), 0.95)

            for node_name, node_output in event.items():
                icon, label = phase_map.get(node_name, ("⚙️", node_name))
                progress_bar.progress(progress, text=f"{icon} {label}")

                with log_container:
                    agent_class = {
                        "research_team": "agent-research",
                        "analysis_team": "agent-analysis",
                        "report_team": "agent-report",
                    }.get(node_name, "")

                    if isinstance(node_output, dict) and show_details:
                        msgs = node_output.get("messages", [])
                        if msgs:
                            last = msgs[-1]
                            agent_name = getattr(last, "name", node_name)
                            content = getattr(last, "content", str(last))
                            preview = content[:300].replace("\n", " ")
                            if len(content) > 300:
                                preview += "..."
                            preview = bleach.clean(
                                preview,
                                tags=_ALLOWED_TAGS,
                                attributes=_ALLOWED_ATTRS,
                                strip=True,
                            )
                            st.markdown(
                                f"<div class='agent-msg {agent_class}'>"
                                f"<strong>{icon} {agent_name}</strong>: {preview}"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown(
                            f"<div class='agent-msg {agent_class}'>"
                            f"<strong>{icon} {node_name}</strong> — 已完成"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

        progress_bar.progress(1.0, text="✅ 完成!")

        st.success(f"✅ 研究完成! 话题: **{topic}**")

        report_files = sorted(OUTPUT_DIR.glob("*"))
        if report_files:
            st.subheader("📁 生成的文件")
            for f in report_files:
                if f.is_file():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if f.suffix == ".md":
                            st.markdown(f"📄 **{f.name}**")
                        elif f.suffix == ".png":
                            st.markdown(f"📊 **{f.name}**")
                        else:
                            st.markdown(f"📎 **{f.name}**")
                    with col2:
                        size_kb = f.stat().st_size / 1024
                        st.caption(f"{size_kb:.1f} KB")

                    if f.suffix == ".md":
                        with st.expander(f"预览: {f.name}"):
                            content = f.read_text()
                            st.markdown(content[:5000])

                    if f.suffix == ".png":
                        with st.expander(f"查看: {f.name}"):
                            st.image(str(f))

        st.balloons()

    except Exception as e:
        st.error(f"❌ 错误: {e}")
        import traceback
        with st.expander("错误详情"):
            st.code(traceback.format_exc())

    st.session_state.running = False

elif run_button and not topic:
    st.warning("请输入研究话题。")

# ── 页脚 ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Contelix v0.2.0 — LangGraph + Streamlit | "
           "多智能体竞争情报平台")
