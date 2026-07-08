"""
Contelix Streamlit Web UI — interactive competitive intelligence research.

Run with:
    streamlit run contelix/ui/streamlit_app.py
    or: contelix run-ui
"""

import sys
from pathlib import Path

import bleach
import streamlit as st

# Allowed HTML tags and attributes for sanitized agent output
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

# Ensure the project root is on the path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from contelix.config import (
    validate_config,
    OUTPUT_DIR,
    MAX_RECURSION_LIMIT,
)
from contelix.agents.supervisor import build_top_graph

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Contelix — Competitive Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ─────────────────────────────────────────────────────────────────
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
.agent-supervisor { background-color: #fff3e0; border-left: 4px solid #ff9800; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "running" not in st.session_state:
    st.session_state.running = False
if "graph" not in st.session_state:
    st.session_state.graph = None

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 Contelix")
    st.caption("AI-Powered Competitive Intelligence")

    st.divider()

    # API status
    if validate_config():
        st.success("✅ API configured")
    else:
        st.error("⚠️ API keys missing")
        st.caption("Set env vars or create .env file")

    st.divider()

    # Settings
    st.subheader("⚙️ Settings")
    recursion = st.slider("Max steps", 50, 300, MAX_RECURSION_LIMIT, step=10)
    show_details = st.checkbox("Show agent details", value=True)

    st.divider()

    # Info
    st.subheader("ℹ️ About")
    st.markdown("""
    **Contelix** uses a multi-agent AI system to:
    1. 🔍 **Research** — Search the web
    2. 📊 **Analyze** — SWOT, trends, comparison
    3. 📝 **Report** — Professional report

    Built with LangGraph + Qwen2.5
    """)

    st.divider()

    st.caption(f"Output: `{OUTPUT_DIR}`")

# ── Main UI ────────────────────────────────────────────────────────────────
st.title("🔍 Competitive Intelligence Research")
st.caption("Enter a company, product, or industry to research. "
           "The AI agent team will search, analyze, and produce a report.")

# Input area
col1, col2 = st.columns([5, 1])
with col1:
    topic = st.text_input(
        "Research Topic",
        placeholder="e.g., Tesla's competitive position in the global EV market",
        label_visibility="collapsed",
        key="topic_input",
    )
with col2:
    run_button = st.button("🚀 Research", type="primary", use_container_width=True)

# Example topics
with st.expander("💡 Example topics"):
    st.markdown("""
    - Tesla's competitive position in the global EV market
    - OpenAI vs Google vs Anthropic AI strategy comparison
    - Cloud infrastructure market: AWS vs Azure vs GCP in 2024
    - Apple Vision Pro competitive landscape and market impact
    - Stripe vs Adyen vs Square: payment platform comparison
    """)

# ── Run research ───────────────────────────────────────────────────────────
if run_button and topic:
    if not validate_config():
        st.error("⚠️ API keys not configured. Set CONTELIX_MODEL_API_KEY and search keys.")
        st.stop()

    st.session_state.running = True
    st.session_state.messages = []

    # Progress containers
    status_area = st.empty()
    progress_bar = st.progress(0, text="Starting...")
    log_container = st.container()

    with log_container:
        st.subheader("📋 Agent Activity Log")

    # Build graph
    with st.spinner("Building agent pipeline..."):
        graph = build_top_graph()

    # Run the pipeline with streaming
    phase_map = {
        "supervisor": ("🧠", "Supervisor routing..."),
        "research_team": ("🔍", "Researching (web search + scraping)..."),
        "analysis_team": ("📊", "Analyzing (SWOT + trends + comparison)..."),
        "report_team": ("📝", "Writing report (outline + content + charts)..."),
    }

    event_index = 0
    total_phases = 4

    try:
        for event in graph.stream(
            {"topic": topic, "messages": [{"role": "user", "content": topic}]},
            {"recursion_limit": recursion},
            subgraphs=True,
        ):
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
                        "supervisor": "agent-supervisor",
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
                            # Sanitize LLM output to prevent XSS
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
                            f"<strong>{icon} {node_name}</strong> — completed"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

        progress_bar.progress(1.0, text="✅ Complete!")

        # Show results
        st.success(f"✅ Research complete! Topic: **{topic}**")

        report_files = sorted(OUTPUT_DIR.glob("*"))
        if report_files:
            st.subheader("📁 Generated Files")
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

                    # Preview report
                    if f.suffix == ".md":
                        with st.expander(f"Preview: {f.name}"):
                            content = f.read_text()
                            st.markdown(content[:5000])

                    if f.suffix == ".png":
                        with st.expander(f"View: {f.name}"):
                            st.image(str(f))

        st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        with st.expander("Error details"):
            st.code(traceback.format_exc())

    st.session_state.running = False

elif run_button and not topic:
    st.warning("Please enter a research topic.")

# ── Footer ─────────────────────────────────────────────────────────────────
st.divider()
st.caption("Contelix v0.1.0 — Built with LangGraph + Streamlit | "
           "Multi-Agent Competitive Intelligence Platform")
