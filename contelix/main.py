#!/usr/bin/env python3
"""
Contelix — AI 竞争情报自动化平台.

用法:
    python -m contelix.main research "研究话题"
    python -m contelix.main research "研究话题" --verbose
    python -m contelix.main research "研究话题" --output ./my_reports
    python -m contelix.main run-ui
    python -m contelix.main run-api

环境配置:
    设置 CONTELIX_MODEL_API_KEY 和搜索 API Key，或复制 .env.example 到 .env。
"""

import argparse
import os
import sys
import uuid
from pathlib import Path
from typing import Optional

import structlog

from contelix.config import (
    validate_config,
    print_config,
    get_output_dir,
    MAX_RECURSION_LIMIT,
    ENABLE_DEBUG,
)
from contelix.logging_config import configure_logging
from contelix.agents.supervisor import build_top_graph

logger = structlog.get_logger(__name__)


def run_research(topic: str, verbose: bool = False, output_dir: Optional[str] = None):
    """运行竞争情报研究任务。"""
    if not validate_config():
        sys.exit(1)

    if output_dir:
        os.environ["CONTELIX_OUTPUT_DIR"] = str(Path(output_dir).resolve())

    output_path = get_output_dir()
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("research_started", topic=topic, output_dir=str(output_path))

    print("=" * 60)
    print("  Contelix — 竞争情报 AI 平台")
    print("=" * 60)
    print(f"\n📋 研究话题: {topic}")
    print(f"📁 输出目录: {output_path}")
    if verbose:
        print_config()
    print()

    logger.info("building_pipeline")
    print("🏗️  正在构建多智能体协作管线...")
    graph = build_top_graph()

    print("🚀 启动研究管线...\n")
    print("-" * 60)

    config = {
        "configurable": {"thread_id": str(uuid.uuid4())[:8]},
        "recursion_limit": MAX_RECURSION_LIMIT,
    }

    try:
        for event in graph.stream(
            {"topic": topic, "messages": [{"role": "user", "content": topic}]},
            config,
            subgraphs=True,
        ):
            if isinstance(event, tuple) and len(event) == 2:
                _, event = event

            if verbose:
                for node_name, node_output in event.items():
                    if isinstance(node_output, dict):
                        msgs = node_output.get("messages", [])
                        if msgs:
                            last = msgs[-1]
                            agent = getattr(last, "name", node_name)
                            content = getattr(last, "content", str(last))
                            preview = content[:150].replace("\n", " ")
                            logger.debug(
                                "agent_output",
                                agent=agent,
                                preview=preview,
                            )
                            print(f"  [{agent}] {preview}...")
                    else:
                        print(f"  [{node_name}] {node_output}")
            else:
                agent_labels = {
                    "research_team": "🔍 研究团队工作中",
                    "analysis_team": "📊 分析团队工作中",
                    "report_team": "📝 报告团队工作中",
                }
                for node_name in event:
                    if node_name is None or node_name == "supervisor":
                        continue
                    label = agent_labels.get(node_name, f"⚙️  {node_name}")
                    print(label)

        print("-" * 60)
        print(f"\n✅ 研究完成!")
        print(f"📁 输出目录: {output_path}")

        report_files = list(output_path.glob("*.md"))
        chart_files = list(output_path.glob("*.png"))

        if report_files:
            print(f"\n📄 生成的报告:")
            for f in report_files:
                size_kb = f.stat().st_size / 1024
                print(f"   - {f.name} ({size_kb:.1f} KB)")

        if chart_files:
            print(f"\n📊 生成的图表:")
            for f in chart_files:
                print(f"   - {f.name}")

        logger.info(
            "research_completed",
            topic=topic,
            report_count=len(report_files),
            chart_count=len(chart_files),
        )
        print("\n完成! 🎉")

    except KeyboardInterrupt:
        logger.info("research_interrupted", topic=topic)
        print("\n⚠️  用户中断。")
        sys.exit(1)
    except Exception as e:
        logger.error("research_failed", topic=topic, error=str(e))
        print(f"\n❌ 错误: {e}")
        if ENABLE_DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def run_ui():
    """启动 Streamlit Web 界面。"""
    import subprocess
    ui_path = Path(__file__).parent / "ui" / "streamlit_app.py"

    if not ui_path.exists():
        print(f"❌ 找不到 UI 文件: {ui_path}")
        sys.exit(1)

    print("🚀 正在启动 Contelix Web 界面...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(ui_path)])


def run_api():
    """启动 FastAPI 服务。"""
    import subprocess
    print("🚀 正在启动 Contelix API → http://0.0.0.0:8000 ...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "contelix.api.app:app",
         "--host", "0.0.0.0", "--port", "8000"]
    )


def main():
    """CLI 入口。"""
    configure_logging()

    parser = argparse.ArgumentParser(
        description="Contelix — AI 竞争情报自动化平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m contelix.main research "特斯拉电动车竞争力分析"
  python -m contelix.main research "云计算市场 AWS vs 阿里云" --verbose
  python -m contelix.main research "AI 编程助手对比" --output ./reports
  python -m contelix.main run-ui
  python -m contelix.main run-api
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # research 子命令
    research_parser = subparsers.add_parser("research", help="运行研究任务")
    research_parser.add_argument("topic", help="研究话题或问题")
    research_parser.add_argument(
        "--output", "-o",
        default=None,
        help="报告输出目录（默认: ./output）",
    )
    research_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细的 Agent 执行过程",
    )

    # run-ui 子命令
    subparsers.add_parser("run-ui", help="启动 Streamlit Web 界面")

    # run-api 子命令
    subparsers.add_parser("run-api", help="启动 FastAPI 服务")

    args = parser.parse_args()

    if args.command == "research":
        run_research(args.topic, verbose=args.verbose, output_dir=args.output)
    elif args.command == "run-ui":
        run_ui()
    elif args.command == "run-api":
        run_api()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
