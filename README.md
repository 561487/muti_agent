# 🔍 Contelix — AI-Powered Competitive Intelligence Platform

> **Multi-Agent System for Automated Competitive Research, Analysis & Reporting**
>
> Built with LangGraph · Qwen2.5 · Streamlit

---

## What is Contelix?

Contelix is a **multi-agent AI system** that automates competitive intelligence research. Given a company, product, or industry topic, it orchestrates a team of specialized AI agents to:

1. **🔍 Research** — Search the web and scrape detailed content from multiple sources
2. **📊 Analyze** — Perform SWOT analysis, trend identification, and competitive comparison
3. **📝 Report** — Generate a professional, structured competitive intelligence report with charts

The system uses a **three-tier hierarchical agent architecture** where each tier is managed by an LLM-based supervisor that routes tasks to specialized sub-agents.

---

## 🏗️ Architecture

```
User Input (Topic)
       │
       ▼
┌─────────────────┐
│  Top Supervisor │  ← "Chief CI Officer" — routes between teams
│   (LangGraph)   │
└────┬───────┬────┘
     │       │
     ▼       ▼
┌─────────┐ ┌──────────┐
│Research │ │Analysis  │
│  Team   │ │  Team    │    Each team = independent LangGraph StateGraph
│  ┌────┐ │ │  ┌─────┐ │    with its own Supervisor managing:
│  │Search│ │ │SWOT   │ │
│  │Scraper│ │ │Trend  │ │    • ReAct agents with specialized tools
│  └────┘ │ │ │Compare│ │    • Supervisor → Agent → Supervisor routing
└─────────┘ │  └─────┘ │
            └──────────┘
                  │
                  ▼
            ┌──────────┐
            │ Report   │
            │  Team    │
            │  ┌─────┐ │
            │  │Outline│
            │  │Writer │
            │  │Chart  │
            │  │Editor │
            │  └─────┘ │
            └──────────┘
                  │
                  ▼
          Final Report (.md)
          + Charts (.png)
```

### Agent Orchestration Pattern

Each team follows the **Supervisor-Worker** pattern:

1. **Supervisor Node** — LLM-powered router decides which specialist to call next
2. **Specialist Agent** — ReAct agent with dedicated tools performs its task
3. **Command(goto="supervisor")** — Agent returns results and control to supervisor
4. **FINISH** — Supervisor signals when the team's work is complete

The top-level graph chains three teams in sequence: Research → Analysis → Report.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- An LLM API key (Alibaba Bailian / OpenAI / compatible)
- A search API key (BochaAI or Tavily)

### Installation

```bash
# Clone and enter the project
cd muti_agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp contelix/.env.example .env
# Edit .env with your API keys
```

### CLI Usage

```bash
# Run a research task
python -m contelix research "Tesla competitive position in EV market"

# With verbose output (see agent decision-making)
python -m contelix research "Cloud market AWS vs Azure vs GCP" --verbose

# Custom output directory
python -m contelix research "AI coding assistants comparison" --output ./my_reports

# Launch web UI
python -m contelix run-ui
# or: streamlit run contelix/ui/streamlit_app.py
```

### Docker

```bash
# Web UI
docker-compose up contelix

# CLI one-shot task
docker-compose --profile cli run contelix-cli research "OpenAI strategy 2024"
```

---

## 📊 Example Output

After running a research task, the `output/` directory contains:

```
output/
├── analysis_swot.md                          # SWOT analysis
├── analysis_trend.md                         # Market trends
├── analysis_comparison.md                    # Competitive comparison
├── report_outline.txt                        # Report structure
├── competitive_intelligence_report.md         # Final polished report
└── market_share_comparison.png               # Generated chart
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Agent Framework** | LangGraph (StateGraph, Command, create_react_agent) |
| **LLM** | Qwen2.5-72B-Instruct (Alibaba Bailian) — configurable to any OpenAI-compatible API |
| **Search** | BochaAI Web Search API / Tavily Search API |
| **Web Scraping** | LangChain WebBaseLoader + BeautifulSoup |
| **Data Analysis** | Python REPL, pandas, numpy |
| **Visualization** | matplotlib |
| **UI** | Streamlit |
| **Deployment** | Docker + docker-compose |

---

## 📁 Project Structure

```
contelix/
├── main.py                    # CLI entry point
├── config.py                  # Environment-based configuration
├── agents/
│   ├── supervisor.py          # Top-level orchestration graph
│   ├── research/
│   │   └── supervisor.py      # Research Team (search + scrape)
│   ├── analysis/
│   │   └── supervisor.py      # Analysis Team (SWOT + trend + compare)
│   └── reporting/
│       └── supervisor.py      # Report Team (outline + write + chart + edit)
├── state/
│   ├── schemas.py             # State type definitions
│   └── supervisor_factory.py  # Reusable supervisor node factory
├── tools/
│   ├── search.py              # Web search tools (BochaAI, Tavily)
│   ├── scraping.py            # Web scraping tools
│   ├── file_ops.py            # File I/O tools
│   └── visualization.py       # Chart generation + Python execution
├── ui/
│   └── streamlit_app.py       # Streamlit web interface
└── tests/
    └── test_tools.py          # Tool unit tests
```

---

## 🔑 Key Design Decisions

- **Hierarchy over Network**: Supervisor pattern ensures coherent multi-step workflows; avoids agent loops
- **Independent StateGraphs per Team**: Each team is a self-contained graph; clean separation of concerns
- **ReAct Agents with Tools**: Agents make autonomous tool-use decisions within their domain
- **Message-based State**: Uses LangGraph's `MessagesState` for natural agent communication
- **Structured Output for Routing**: Supervisors use `with_structured_output()` for reliable JSON routing decisions

---

## 🎯 Future Roadmap

- [ ] ChromaDB integration for caching research (RAG)
- [ ] PDF report generation (via LaTeX or WeasyPrint)
- [ ] Scheduled monitoring (periodic competitive intelligence updates)
- [ ] Slack/Discord bot integration for on-demand research
- [ ] Multi-language search and report generation
- [ ] Competitive landscape interactive dashboard

---

## 📝 License

MIT License — use freely for personal and commercial projects.

---

*Built for demonstrating multi-agent AI engineering skills in production-grade agentic applications.*
