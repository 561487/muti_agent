# Contelix — AI 竞争情报平台

> **多智能体 AI 系统，自动完成竞争情报的搜索、分析与报告生成**
>
> **Multi-Agent System for Automated Competitive Research, Analysis & Reporting**
>
> Built with LangGraph · Qwen2.5 · FastAPI · Streamlit

---

## 这是什么？ / What is Contelix?

Contelix 是一个**多层次多智能体 AI 系统**，输入一个公司、产品或行业话题，自动调度 8 个专业 AI Agent 完成：

1. **搜索** — 多源网络搜索与内容抓取
2. **分析** — SWOT 分析、趋势识别、竞品对比
3. **报告** — 生成结构化专业竞争情报报告（含图表）

Contelix is a **multi-agent AI system** that automates competitive intelligence research. Given a topic, it orchestrates 8 specialized agents across a 3-tier architecture to search, analyze, and report.

---

## 架构 / Architecture

```
User Input (Topic) / 用户输入
       │
       ▼
┌──────────────┐
│   Research   │  search_agent + scraper_agent
│    Team      │  BochaAI / Tavily + WebBaseLoader
└──────┬───────┘
       │ research findings
       ▼
┌──────────────┐
│   Analysis   │  swot_analyst + trend_analyst + comparison_analyst
│    Team      │  SWOT · 趋势 · 竞品对比
└──────┬───────┘
       │ analysis results
       ▼
┌──────────────┐
│   Report     │  outline_writer + content_writer
│    Team      │  + chart_generator + editor
└──────┬───────┘
       │
       ▼
  Final Report (.md)
  + Charts (.png)
```

**Top-level pipeline**: Simple sequential chain — no unnecessary LLM routing overhead.

**Team internals**: Each team uses the **Supervisor-Worker** pattern with an LLM-based router managing ReAct agents with specialized tools.

---

## 快速开始 / Quick Start

### 环境要求 / Prerequisites

- Python 3.11+
- LLM API Key（阿里百炼 / OpenAI / 兼容接口）
- 搜索 API Key（BochaAI 或 Tavily）

### 安装 / Installation

```bash
cd muti_agent
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入你的 API Keys
```

### CLI 使用

```bash
# 运行研究任务
python -m contelix research "Tesla 在全球电动车市场的竞争地位"

# 详细输出（查看 Agent 决策过程）
python -m contelix research "云计算市场 AWS vs Azure vs GCP" --verbose

# 自定义输出目录
python -m contelix research "AI 编程助手对比" --output ./my_reports

# 启动 Web UI
python -m contelix run-ui

# 启动 API 服务
python -m contelix run-api
```

### API 使用 / API Usage

```bash
# 提交研究任务
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "Tesla EV competitive analysis"}'

# 查询任务状态
curl http://localhost:8000/research/{task_id}

# 健康检查
curl http://localhost:8000/health
```

### Docker

```bash
# Web UI
docker-compose up contelix

# CLI 一次性任务
docker-compose --profile cli run contelix-cli research "OpenAI 战略分析"
```

---

## 示例输出 / Example Output

运行研究任务后，`output/` 目录会生成：

```
output/
├── analysis_swot.md                       # SWOT 分析
├── analysis_trend.md                      # 市场趋势
├── analysis_comparison.md                 # 竞品对比
├── report_outline.txt                     # 报告大纲
├── competitive_intelligence_report.md     # 最终报告
└── market_share_comparison.png            # 可视化图表
```

---

## 技术栈 / Technology Stack

| 层级 / Layer | 技术 / Technology |
|-------------|-------------------|
| **Agent 框架** | LangGraph 1.x (StateGraph, Command, create_react_agent) |
| **LLM** | Qwen2.5-72B-Instruct（阿里百炼）— 可替换任意 OpenAI 兼容 API |
| **搜索** | BochaAI / Tavily 双后端，自动 fallback |
| **网页抓取** | LangChain WebBaseLoader + BeautifulSoup |
| **数据分析** | 子进程沙箱 Python 执行环境（安全隔离） |
| **可视化** | matplotlib |
| **API** | FastAPI |
| **UI** | Streamlit |
| **可观测性** | structlog 结构化日志 + LangSmith tracing |
| **持久化** | Memory / SQLite / PostgreSQL 检查点 |
| **部署** | Docker + docker-compose |

---

## 项目结构 / Project Structure

```
contelix/
├── main.py                       # CLI 入口（research / run-ui / run-api）
├── config.py                     # 环境变量驱动配置
├── llm_factory.py                # 线程安全 LLM 工厂
├── logging_config.py             # structlog 结构化日志配置
├── retry.py                      # RetryPolicy 配置
├── agents/
│   ├── supervisor.py             # 顶层编排（Research → Analysis → Report）
│   ├── node_factory.py           # 共享 Agent 节点工厂（含错误处理）
│   ├── research/supervisor.py    # Research Team（search + scraper）
│   ├── analysis/supervisor.py    # Analysis Team（SWOT + trend + comparison）
│   └── reporting/supervisor.py   # Report Team（outline + write + chart + edit）
├── state/
│   ├── schemas.py                # State 类型定义
│   └── supervisor_factory.py     # 可复用 Supervisor 节点工厂
├── tools/
│   ├── search.py                 # 网络搜索工具
│   ├── scraping.py               # 网页抓取工具
│   ├── file_ops.py               # 文件 I/O 工具（含路径穿越保护）
│   ├── visualization.py          # 图表生成 + 沙箱 Python 执行
│   └── sandbox.py                # 子进程沙箱（RCE 防护）
├── checkpoint/
│   └── manager.py                # 检查点管理（memory/sqlite/postgres）
├── api/
│   ├── app.py                    # FastAPI 应用
│   └── __init__.py
├── ui/
│   └── streamlit_app.py          # Streamlit Web 界面
├── tests/
│   ├── conftest.py               # 共享 fixtures
│   ├── test_tools.py             # 文件操作测试
│   ├── test_search.py            # 搜索工具测试
│   ├── test_scraping.py          # 抓取工具测试
│   ├── test_visualization.py     # 可视化 + 沙箱安全测试
│   └── test_config.py            # 配置验证测试
└── docs/
    └── contelix-design-doc.md    # 设计文档
```

---

## 设计决策 / Key Design Decisions

- **固定流水线顶层**：顶层不再用 LLM 路由，改为确定性的链式调用，节省 LLM 调用次数，消除路由失败风险
- **层级 Supervisor 模式**：每个 Team 内部采用 LLM 路由的 Supervisor-Worker 模式，Agent 自主决策工具调用
- **独立 StateGraph**：每个 Team 是自包含的编译子图，职责清晰、互不污染
- **子进程沙箱**：LLM 生成的 Python 代码在 import 白名单 + 文件访问受限的子进程中执行
- **路径穿越保护**：所有文件操作经过 `_resolve_safe_path()` 校验
- **结构化日志**：`structlog` 终端彩色输出 / 管道 JSON 输出，兼容 ELK/Loki
- **检查点持久化**：支持 Memory / SQLite / PostgreSQL 三种后端，崩溃后可恢复
- **线程安全 LLM 工厂**：按 (model, temperature) 缓存实例，支持并发图执行

---

## 安全 / Security

| 防护 | 实现 |
|------|------|
| RCE 防护 | 子进程沙箱，import 白名单，无 `os`/`subprocess`/`socket` |
| 路径穿越 | `_resolve_safe_path()` 拦截 `../` 和绝对路径 |
| XSS 防护 | `bleach` HTML 清洗，仅允许安全标签 |
| API Key 泄露 | 异常信息脱敏，`.gitignore` 排除 `.env` |

---

## 测试 / Tests

```bash
pytest contelix/tests/ -v        # 32 tests: tools, search, scraping, viz, sandbox, config
```

---

## 路线图 / Roadmap

- [ ] ChromaDB 集成（RAG 缓存研究结果）
- [ ] PDF 报告生成（LaTeX / WeasyPrint）
- [ ] CI/CD Pipeline（GitHub Actions）
- [ ] 定时监控（周期性竞争情报更新）
- [ ] Slack/Discord Bot 集成
- [ ] 多语言搜索与报告生成
- [ ] 竞争格局交互式仪表板

---

## 许可证 / License

MIT License — 个人和商业项目均可自由使用。

---

*一个展示生产级多智能体 AI 工程能力的项目。Built for demonstrating production-grade multi-agent AI engineering.*
