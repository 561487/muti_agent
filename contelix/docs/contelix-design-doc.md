# Contelix — AI 竞争情报自动化平台 设计文档

> **版本**: v0.1.0 | **作者**: stu02 | **日期**: 2026-06-30
>
> 基于 LangGraph 的多智能体系统，自动完成竞争情报的搜索、分析与报告生成。

---

## 目录

1. [项目概述](#1-项目概述)
2. [业务场景](#2-业务场景)
3. [系统架构](#3-系统架构)
4. [智能体设计](#4-智能体设计)
5. [状态管理](#5-状态管理)
6. [工具层](#6-工具层)
7. [核心设计模式](#7-核心设计模式)
8. [代码结构](#8-代码结构)
9. [部署与运行](#9-部署与运行)
10. [技术选型理由](#10-技术选型理由)

---

## 1. 项目概述

### 1.1 一句话定义

Contelix 是一个 **AI 驱动的竞争情报（Competitive Intelligence）自动化平台**。用户输入一个公司名或行业话题，系统自动调度多个专业 AI Agent，完成：

```
信息搜索 → 网页抓取 → SWOT 分析 → 趋势识别 → 竞品对比 → 报告撰写 → 图表生成 → 编辑润色
```

10-15 分钟内产出可直接呈报管理层的专业竞争情报报告。

### 1.2 核心特性

- **多智能体协作**: 8 个专业 Agent，三层 Supervisor 架构
- **自主工具调用**: 每个 Agent 独立决策何时搜索、抓取、写文件、跑代码
- **LLM 动态路由**: Supervisor 根据上下文智能决策下一步行动，非硬编码流程
- **流式可视化**: Streamlit Web UI 实时展示 Agent 工作过程
- **可扩展架构**: 新增 Agent 只需注册到 Supervisor 的成员列表
- **生产级工程**: Docker 部署、环境变量管理、单元测试覆盖

### 1.3 演示示例

```bash
# 输入
python -m contelix research "Tesla competitive position in EV market"

# 10-15分钟后，output/ 目录产出:
#   competitive_intelligence_report.md  ← 最终报告
#   analysis_swot.md                    ← SWOT 分析
#   analysis_trend.md                   ← 趋势分析
#   analysis_comparison.md              ← 竞品对比
#   competitor_comparison_chart.png     ← 对比图表
```

---

## 2. 业务场景

### 2.1 目标用户

| 角色 | 场景 | 价值 |
|------|------|------|
| 产品经理 | 研究竞品功能、定价策略 | 省去 2-3 天手工调研 |
| 战略分析师 | 行业趋势、市场格局分析 | 快速获取结构化洞察 |
| 创业者/投资人 | 目标市场尽职调查 | 全面了解竞争格局 |
| 市场运营 | 竞品动态监控 | 持续跟踪对手动向 |

### 2.2 典型查询

```
"OpenAI vs Google vs Anthropic AI 战略对比"
"云计算市场 AWS vs Azure vs GCP 2024 年格局"
"Apple Vision Pro 竞品格局与市场影响"
"Stripe vs Adyen vs Square 支付平台对比"
"特斯拉在全球电动车市场的竞争地位"
"AI 代码助手赛道：GitHub Copilot vs Cursor vs Codeium"
```

### 2.3 与传统方式对比

| 维度 | 人工调研 | Contelix |
|------|---------|----------|
| 耗时 | 2-3 天 | 10-15 分钟 |
| 搜索覆盖面 | 受限于个人精力 | 多轮多角度搜索 |
| 分析维度 | 依赖个人经验 | 固定的 SWOT+趋势+对比框架 |
| 报告格式 | 因人而异 | 统一的专业 markdown 格式 |
| 可复制性 | 低 | 高，换 topic 即跑 |

---

## 3. 系统架构

### 3.1 总体架构图

```
                          ┌──────────────────────────────────┐
                          │         用户输入 (Topic)           │
                          └──────────────┬───────────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────┐
                          │     Top Supervisor        │
                          │   "首席竞争情报官"         │
                          │   LLM 动态路由器           │
                          │   决策: Research /         │
                          │   Analysis / Report /      │
                          │   FINISH                  │
                          └──┬──────────┬────────────┘
                             │          │
              ┌──────────────┘          └──────────────┐
              ▼                                        ▼
   ┌──────────────────────┐              ┌──────────────────────┐
   │   Research Team      │              │   Analysis Team      │
   │   (研究团队)          │              │   (分析团队)          │
   │                      │              │                      │
   │  ┌────────────────┐  │              │  ┌────────────────┐  │
   │  │   Supervisor   │  │              │  │   Supervisor   │  │
   │  │   (路由器)      │  │              │  │   (路由器)      │  │
   │  └───┬──────┬─────┘  │              │  └───┬──────┬─────┘  │
   │      │      │        │              │      │      │        │
   │  ┌───┴┐  ┌──┴───┐    │              │  ┌───┴┐ ┌──┴──┐ ┌───┴──┐
   │  │Search│ │Scraper│   │              │  │SWOT│ │Trend│ │Compare│
   │  │搜索  │ │抓取   │   │              │  │分析│ │分析 │ │对比  │
   │  └─────┘ └──────┘   │              │  └────┘ └─────┘ └──────┘
   └──────────────────────┘              └──────────────────────┘
                             │          │
                             └────┬─────┘
                                  ▼
                       ┌──────────────────────┐
                       │   Report Team        │
                       │   (报告团队)          │
                       │                      │
                       │  ┌────────────────┐  │
                       │  │   Supervisor   │  │
                       │  │   (路由器)      │  │
                       │  └──┬──┬──┬──────┘  │
                       │     │  │  │         │
                       │  ┌──┴┐┌┴┐┌┴───┐┌──┴──┐
                       │  │Out-│ │Chart│ │     │
                       │  │line│ │     │ │Edit │
                       │  │大纲│ │图表 │ │编辑 │
                       │  └───┘└─────┘└─────┘
                       │  ┌──────┐            │
                       │  │Writer│            │
                       │  │写作  │            │
                       │  └──────┘            │
                       └──────────────────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │  最终产出              │
                       │  • report.md          │
                       │  • charts/*.png       │
                       │  • analysis_*.md      │
                       └──────────────────────┘
```

### 3.2 三层 Team 职责

| 层级 | Team | 输入 | 输出 | 内部 Agent 数 |
|------|------|------|------|:---:|
| L1 | Research | 用户 topic | 结构化的研究简报 | 2 (Search + Scraper) |
| L2 | Analysis | 研究简报 | SWOT/趋势/对比分析 | 3 (SWOT + Trend + Compare) |
| L3 | Report | 分析结果 | 专业报告 + 图表 | 4 (Outline + Writer + Chart + Editor) |

### 3.3 执行流程

```
START
  │
  ▼
Top Supervisor ──→ research_team ──→ Top Supervisor
                                        │
                                        ▼
                                  analysis_team ──→ Top Supervisor
                                                        │
                                                        ▼
                                                  report_team ──→ Top Supervisor
                                                                        │
                                                                        ▼
                                                                      FINISH
                                                                        │
                                                                        ▼
                                                                       END
```

每个 Team 内部又有自己的 Supervisor-Agent 循环：

```
Team Supervisor ──→ Agent A ──→ Team Supervisor
       │                              │
       │              ┌───────────────┘
       │              ▼
       │         Agent B ──→ Team Supervisor
       │                              │
       └──────────────────────────────┘
                      │
                      ▼
                   FINISH
```

---

## 4. 智能体设计

### 4.1 智能体总览

| # | Agent 名称 | 所属 Team | 工具 | 核心职责 |
|:--:|-----------|----------|------|---------|
| 1 | Search Agent | Research | `competitive_search`, `search_news` | 多轮多角度搜索，发现相关网页和新闻 |
| 2 | Scraper Agent | Research | `scrape_webpages` | 抓取搜索结果 URL 的网页全文 |
| 3 | SWOT Analyst | Analysis | `save_analysis` | 优势/劣势/机会/威胁四维分析 |
| 4 | Trend Analyst | Analysis | `save_analysis` | 行业趋势、技术变化、监管动向 |
| 5 | Comparison Analyst | Analysis | `save_analysis` | 竞品功能/定价/市场份额对比 |
| 6 | Outline Writer | Report | `create_outline`, `read_document` | 规划报告结构和章节大纲 |
| 7 | Content Writer | Report | `write_document`, `read_document`, `edit_document` | 撰写完整报告正文 |
| 8 | Chart Generator | Report | `execute_python`, `generate_comparison_chart` | 用 Python/matplotlib 生成图表 |
| 9 | Editor | Report | `read_document`, `edit_document` | 审查报告质量，编辑润色 |

### 4.2 Agent 实现方式

每个 Agent 使用 **ReAct (Reasoning + Acting)** 模式：

```python
# 伪代码示意
search_agent = create_react_agent(
    llm,                           # Qwen2.5-72B-Instruct
    tools=[competitive_search, search_news],
    prompt=(
        "You are a competitive intelligence researcher. "
        "Search the web and return structured summaries."
    ),
)
```

ReAct Agent 的核心循环：

```
1. LLM 接收消息 → 思考下一步
2. 需要搜索？→ 调用 competitive_search 工具
3. 工具返回搜索结果 → LLM 分析结果
4. 还需要更多？→ 换关键词再搜
5. 信息够了 → 返回结构化摘要给 Supervisor
```

### 4.3 Agent 节点包装

每个 ReAct Agent 被包装成 LangGraph 节点函数：

```python
def search_node(state: ResearchState) -> Command[Literal["supervisor"]]:
    """搜索节点 — 执行搜索后返回 Supervisor"""
    result = search_agent.invoke(state)
    last_msg = result["messages"][-1]
    return Command(
        update={
            "messages": [
                HumanMessage(content=last_msg.content, name="search_agent")
            ]
        },
        goto="supervisor",  # ← 关键：完事后交还控制权
    )
```

### 4.4 Supervisor 节点

Supervisor 是一个 **LLM 驱动的路由器**，不是写死的流程控制：

```python
class Router(TypedDict):
    """下一个路由目标"""
    next: Literal["search_agent", "scraper_agent", "FINISH"]

def supervisor_node(state):
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]  # LLM 动态决策！
    if goto == "FINISH":
        goto = END
    return Command(goto=goto)
```

**为什么不用 if-else？** 因为对话上下文复杂多变——Search Agent 返回的结果质量好坏不同，可能需要让它再搜一次，也可能直接进入抓取。LLM 能根据实际情况做判断。

---

## 5. 状态管理

### 5.1 状态分层设计

每个 Team 有独立的状态 Schema，相互隔离：

#### ResearchState（研究状态）

```python
class ResearchState(MessagesState):
    research_topic: str         # 研究主题
    search_results: List[dict]  # 搜索结果列表
    scraped_content: str        # 抓取的网页内容
    research_summary: str       # 研究摘要
```

#### AnalysisState（分析状态）

```python
class AnalysisState(MessagesState):
    research_data: str          # 研究数据（来自 Research Team）
    swot_result: str            # SWOT 分析输出
    trend_result: str           # 趋势分析输出
    comparison_result: str      # 竞品对比输出
```

#### ReportState（报告状态）

```python
class ReportState(MessagesState):
    analysis_data: str          # 分析数据（来自 Analysis Team）
    topic: str                  # 原始主题
    report_outline: List[str]   # 报告大纲
    report_content: str         # 报告正文
    charts: List[str]           # 图表路径
    final_report_path: str      # 最终报告路径
```

#### OverallState（全局状态）

```python
class OverallState(MessagesState):
    topic: str                  # 用户话题
    next_team: str              # 路由目标
    research_complete: bool     # 研究是否完成
    analysis_complete: bool     # 分析是否完成
    report_complete: bool       # 报告是否完成
    output_dir: str             # 输出目录
```

### 5.2 消息传递机制

Team 之间通过消息传递数据，而非直接访问对方的状态：

```
Research Team 完成 → 返回 HumanMessage(name="research_team", content=研究摘要)
                      ↓
Top Supervisor 收到  → 提取 content，传给 Analysis Team
                      ↓
Analysis Team 完成  → 返回 HumanMessage(name="analysis_team", content=分析结果)
                      ↓
Top Supervisor 收到  → 提取 content，传给 Report Team
```

```python
# Top Supervisor 中的 Team 调用节点
def call_research_team(state: OverallState):
    # 1. 调用子图
    response = research_graph.invoke({"messages": [HumanMessage(...)]})

    # 2. 把结果以命名的 HumanMessage 返回
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response["messages"][-1].content,
                    name="research_team"  # ← 标记来源
                )
            ],
            "research_complete": True,
        },
        goto="supervisor",
    )

def call_analysis_team(state: OverallState):
    # 3. 从消息历史中提取 Research Team 的结果
    research_content = ""
    for msg in state["messages"]:
        if hasattr(msg, "name") and msg.name == "research_team":
            research_content = msg.content
            break

    # 4. 传给 Analysis Team
    response = analysis_graph.invoke(
        {"messages": [HumanMessage(content=research_content)]}
    )
    # ...
```

### 5.3 Reducer 机制

使用 LangGraph 的 `add_messages` reducer 自动合并消息列表：

```python
from langgraph.graph.message import add_messages

class State(MessagesState):
    # messages 字段自动使用 add_messages reducer
    # 新消息追加到列表末尾，而非覆盖
    pass
```

---

## 6. 工具层

### 6.1 工具总览

| 工具名称 | 类型 | 用途 |
|---------|------|------|
| `competitive_search` | 搜索 | 通用竞争情报搜索（BochaAI/Tavily） |
| `search_news` | 搜索 | 专搜新闻（内部调用 competitive_search） |
| `scrape_webpages` | 抓取 | 批量抓取 URL 网页全文 |
| `extract_key_info` | 抓取 | 抓取单页面并标注关注领域 |
| `create_outline` | 文件 | 创建报告大纲文件 |
| `write_document` | 文件 | 创建/覆盖文档 |
| `read_document` | 文件 | 读取文档内容（支持行范围） |
| `edit_document` | 文件 | 在指定行号插入文本 |
| `list_output_files` | 文件 | 列出输出目录所有文件 |
| `execute_python` | 分析 | 执行 Python 代码（含 matplotlib） |
| `generate_comparison_chart` | 分析 | 从 JSON 数据生成对比图表 |
| `save_analysis` | 分析 | 保存分析结果到文件 |

### 6.2 搜索工具实现

支持双后端自动切换：

```python
@tool
def competitive_search(query: str, num_results: int = 8) -> str:
    # 优先使用 Tavily
    if TAVILY_API_KEY:
        try:
            tavily = TavilySearchResults(max_results=num_results)
            return tavily.invoke({"query": query})
        except Exception:
            pass  # 失败则降级

    # 降级到 BochaAI
    results = _bocha_search(query, count=num_results)

    # 统一格式返回
    lines = []
    for r in results:
        lines.append(f"**{r['title']}**\n{r['snippet']}\nURL: {r['url']}")
    return "\n\n".join(lines)
```

### 6.3 图表生成工具

Agent 可以自主写 Python 代码生成可视化：

```python
# Chart Generator Agent 会自主写出类似代码：
import matplotlib.pyplot as plt
import numpy as np

companies = ['Tesla', 'BYD', 'VW', 'NIO', 'Xpeng']
market_share = [21.4, 18.2, 15.8, 5.3, 3.9]

plt.figure(figsize=(10, 6))
plt.bar(companies, market_share, color='steelblue')
plt.title('Global EV Market Share 2024')
plt.ylabel('Market Share (%)')
plt.tight_layout()
plt.savefig('output/ev_market_share.png', dpi=150)
```

通过 `execute_python` 工具在安全沙箱（PythonREPL）中执行。

---

## 7. 核心设计模式

### 7.1 Supervisor-Worker 模式

整个项目最核心的编排模式：

```
                 ┌──────────────┐
      ┌──────────│  Supervisor  │──────────┐
      │          │  (LLM 路由)   │          │
      │          └──────────────┘          │
      ▼                 ▲                  ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│ Agent A  │──────│ Agent B  │──────│ Agent C  │
│ (ReAct)  │      │ (ReAct)  │      │ (ReAct)  │
└──────────┘      └──────────┘      └──────────┘
```

- Supervisor 不干活，只负责决策"下一个该谁干"
- 每个 Agent 干完活通过 `Command(goto="supervisor")` 交还控制权
- Supervisor 看全局上下文判断：继续派活 or FINISH

### 7.2 工厂函数模式

`make_supervisor_node()` 是通用工厂，整个项目 4 个 Supervisor 都靠它：

```python
def make_supervisor_node(llm, members, system_prompt=None):
    """一行代码创建任意团队的 Supervisor"""

# 用法: 不同团队只需要不同的成员列表
research_supervisor = make_supervisor_node(llm, ["search", "scraper"])
analysis_supervisor  = make_supervisor_node(llm, ["swot", "trend", "compare"])
report_supervisor    = make_supervisor_node(llm, ["outline", "writer", "chart", "editor"])
top_supervisor       = make_supervisor_node(llm, ["research_team", "analysis_team", "report_team"])
```

### 7.3 独立子图模式

每个 Team 是独立的 `StateGraph`，可以独立编译、独立测试：

```python
# 每个 Team 导出 build_xxx_graph() 函数
def build_research_graph():
    builder = StateGraph(ResearchState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("search", search_node)
    builder.add_node("scraper", scraper_node)
    builder.add_edge(START, "supervisor")
    return builder.compile()

# Top 层按需调用
response = research_graph.invoke({"messages": [...]})
```

### 7.4 Structured Output 路由

Supervisor 的路由决策使用 `with_structured_output()` 保证输出可靠性：

```python
class Router(TypedDict):
    next: Literal["search_agent", "scraper_agent", "FINISH"]

# LLM 强制输出 JSON，不会产生解析错误
response = llm.with_structured_output(Router).invoke(messages)
# response = {"next": "search_agent"}  ← 总是合法的
```

### 7.5 关注点分离

```
Top Supervisor     → 只管流程（谁先谁后）
  ├─ Research Team → 只管信息收集
  ├─ Analysis Team → 只管数据分析
  └─ Report Team   → 只管报告生成

每个 Team 内部:
  Team Supervisor → 只管团队内任务分配
    ├─ Agent A     → 只管自己领域的一件事
    └─ Agent B     → 只管自己领域的一件事
```

---

## 8. 代码结构

```
contelix/
├── main.py                          # CLI 入口
│   ├── run_research(topic)          #   命令行研究任务
│   └── run_ui()                     #   启动 Streamlit UI
│
├── config.py                        # 环境变量配置管理
│   ├── MODEL_NAME / BASE_URL / API_KEY
│   ├── BOCHA_API_KEY / TAVILY_API_KEY
│   └── OUTPUT_DIR / ENABLE_DEBUG / ...
│
├── agents/
│   ├── supervisor.py                # Top 层编排
│   │   ├── call_research_team()     #   调用 Research 子图
│   │   ├── call_analysis_team()     #   调用 Analysis 子图
│   │   ├── call_report_team()       #   调用 Report 子图
│   │   └── build_top_graph()        #   构建顶层 StateGraph
│   │
│   ├── research/
│   │   └── supervisor.py            # Research Team
│   │       ├── _llm                 #   共享 LLM 实例
│   │       ├── _AGENTS              #   ReAct Agent 字典
│   │       ├── _supervisor_node     #   Team Supervisor
│   │       └── build_research_graph()
│   │
│   ├── analysis/
│   │   └── supervisor.py            # Analysis Team
│   │       ├── save_analysis tool
│   │       ├── _AGENTS (SWOT, Trend, Compare)
│   │       └── build_analysis_graph()
│   │
│   └── reporting/
│       └── supervisor.py            # Report Team
│           ├── _AGENTS (Outline, Writer, Chart, Editor)
│           └── build_report_graph()
│
├── state/
│   ├── schemas.py                   # 4 个层级的 State Schema
│   │   ├── ResearchState
│   │   ├── AnalysisState
│   │   ├── ReportState
│   │   └── OverallState
│   │
│   └── supervisor_factory.py        # Supervisor 工厂函数
│       └── make_supervisor_node()
│
├── tools/
│   ├── search.py                    # 搜索工具
│   │   ├── competitive_search()
│   │   └── search_news()
│   │
│   ├── scraping.py                  # 抓取工具
│   │   ├── scrape_webpages()
│   │   └── extract_key_info()
│   │
│   ├── file_ops.py                  # 文件操作
│   │   ├── create_outline()
│   │   ├── write_document()
│   │   ├── read_document()
│   │   ├── edit_document()
│   │   └── list_output_files()
│   │
│   └── visualization.py             # 可视化
│       ├── execute_python()
│       └── generate_comparison_chart()
│
├── ui/
│   └── streamlit_app.py             # Streamlit Web UI
│
├── tests/
│   └── test_tools.py                # 工具层单元测试（5 个）
│
├── docs/
│   └── contelix-design-doc.md       # 本文档
│
├── output/                          # 报告输出目录
├── .env.example                     # 配置模板
└── __init__.py
```

---

## 9. 部署与运行

### 9.1 环境配置

```bash
# 1. 克隆项目
cd muti_agent

# 2. 创建虚拟环境
python -m venv .venv && source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API Keys
cp contelix/.env.example .env
# 编辑 .env 文件，填入:
#   CONTELIX_MODEL_API_KEY=sk-xxx  (阿里百炼)
#   BOCHA_API_KEY=sk-xxx           (BochaAI 搜索)
```

### 9.2 CLI 运行

```bash
# 基础用法
python -m contelix research "特斯拉电动车竞争分析"

# 详细输出（看每个 Agent 的思考过程）
python -m contelix research "Cloud market AWS vs Azure vs GCP" --verbose

# 指定输出目录
python -m contelix research "AI coding assistants comparison" --output ./reports

# 启动 Web UI
python -m contelix run-ui
```

### 9.3 Docker 部署

```bash
# Web UI 模式
docker-compose up contelix
# 访问 http://localhost:8501

# CLI 模式
docker-compose --profile cli run contelix-cli \
  research "OpenAI GPT-5 strategy analysis" --verbose
```

### 9.4 运行测试

```bash
pytest contelix/tests/test_tools.py -v
# 5 passed
```

---

## 10. 技术选型理由

| 技术选择 | 理由 |
|---------|------|
| **LangGraph** | 当前最主流的多 Agent 编排框架，StateGraph + Command 天然支持复杂工作流 |
| **Supervisor 模式** | 相比 Network（去中心化 P2P），Supervisor 有明确的流程控制，适合多步骤业务场景 |
| **Hierarchy 三层** | 相比单层，三层隔离了关注点；相比更多层，三层足够复杂又不过度设计 |
| **ReAct Agent** | 让 Agent 自主决策工具调用，而非死板的 pipeline，适应性更强 |
| **Structured Output** | `with_structured_output()` 强制 JSON 输出，比自由文本解析更可靠 |
| **Qwen2.5-72B** | 国产模型，性价比高，兼容 OpenAI API，可无缝切换 GPT-4o/Claude |
| **Streamlit** | 快速原型 UI，流式展示 Agent 过程，比 Gradio 更灵活 |
| **Message-based 通信** | Agent 间通过消息而非直接访问状态，松耦合，易扩展 |
| **环境变量管理** | 所有密钥通过 .env 注入，零硬编码，符合安全最佳实践 |

---

## 附录 A: 面试讲述指南

当面试官问"你做过什么 AI Agent 项目"，按以下结构讲述：

### 1. 项目背景 (30秒)
> "我独立设计实现了一个竞争情报自动化平台 Contelix。用户输入公司名，系统自动调度多个 AI Agent 完成搜索→分析→报告的全流程。"

### 2. 架构亮点 (2分钟)
> "核心是三层 Hierarchy 多智能体架构。每层有 LLM 驱动的 Supervisor 做动态路由，Agent 用 ReAct 模式自主调用工具。层与层之间通过消息传递数据，完全解耦。
>
> 总共 8 个专业 Agent，4 个 Supervisor，10+ 个工具。整个架构可以用工厂函数快速扩展——加一个新 Agent 只需要注册到 Supervisor 的成员列表。"

### 3. 技术细节 (2分钟)
> "技术栈是 LangGraph + Qwen2.5 + Streamlit。我用了 Structured Output 保证 Supervisor 路由的可靠性，用独立子图保证 Team 间隔离，用 Command 机制实现 Agent 到 Supervisor 的控制流转。
>
> 项目有完整的工程实践：环境变量管理、Docker 部署、单元测试、40 页设计文档。"

### 4. 总结 (30秒)
> "这个项目展示了我在多智能体系统设计、LLM 应用工程化、复杂工作流编排方面的能力。架构思想是关注点分离和可扩展性。"

---

## 附录 B: 未来扩展方向

- [ ] **RAG 记忆**: 用 ChromaDB 缓存已研究过的内容，避免重复搜索
- [ ] **PDF 导出**: 用 WeasyPrint/LaTeX 生成 PDF 格式报告
- [ ] **定时监控**: 用 Cron 触发定时竞品动态跟踪
- [ ] **Slack Bot**: 集成 Slack，@ 一下即可发起研究
- [ ] **多语言**: 中/日/韩多语言搜索和报告生成
- [ ] **交互式仪表盘**: 用 Plotly/Dash 做竞争格局可视化
- [ ] **Deep Research 模式**: 多轮深度搜索（OpenAI Deep Research 风格）
- [ ] **Human-in-the-Loop**: 关键节点（搜索完成/报告草案）暂停等待人工审核

---

> **文档版本**: v1.0 | **最后更新**: 2026-06-30
>
> 本项目为 AI Agent 工程能力展示作品，欢迎用于学习和面试。
