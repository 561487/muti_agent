#!/usr/bin/env python3
"""
Contelix — AI-Powered Competitive Intelligence Automation Platform.

Usage:
    contelix research "Tesla's competitive position in EV market"
    contelix research "OpenAI GPT-5 strategy" --output ./my_reports
    contelix research "Cloud market AWS vs Azure vs GCP" --verbose
    contelix run-ui                          # Launch Streamlit web UI

Environment:
    Set CONTELIX_MODEL_API_KEY and search API keys, or copy .env.example to .env.
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
    """
    Run a competitive intelligence research task.

    Args:
        topic: The research topic/query.
        verbose: If True, print detailed agent progress.
        output_dir: Optional custom output directory.
    """
    if not validate_config():
        sys.exit(1)

    # Set custom output directory before getting the resolved path
    if output_dir:
        os.environ["CONTELIX_OUTPUT_DIR"] = str(Path(output_dir).resolve())

    output_path = get_output_dir()
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(
        "research_started",
        topic=topic,
        output_dir=str(output_path),
    )

    print("=" * 60)
    print("  Contelix — Competitive Intelligence Platform")
    print("=" * 60)
    print(f"\n📋 Research Topic: {topic}")
    print(f"📁 Output Directory: {output_path}")
    if verbose:
        print_config()
    print()

    # Build the orchestration graph
    logger.info("building_pipeline")
    print("🏗️  Building multi-agent pipeline...")
    graph = build_top_graph()

    # Run the pipeline
    print("🚀 Starting research pipeline...\n")
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
                for node_name in event:
                    label = {
                        "research_team": "🔍 Researching...",
                        "analysis_team": "📊 Analyzing...",
                        "report_team": "📝 Writing report...",
                    }.get(node_name, f"⚙️  {node_name}")
                    print(label)

        print("-" * 60)
        print(f"\n✅ Research complete!")
        print(f"📁 Output saved to: {output_path}")

        # Check for generated files
        report_files = list(output_path.glob("*.md"))
        chart_files = list(output_path.glob("*.png"))

        if report_files:
            print(f"\n📄 Generated Reports:")
            for f in report_files:
                size_kb = f.stat().st_size / 1024
                print(f"   - {f.name} ({size_kb:.1f} KB)")

        if chart_files:
            print(f"\n📊 Generated Charts:")
            for f in chart_files:
                print(f"   - {f.name}")

        logger.info(
            "research_completed",
            topic=topic,
            report_count=len(report_files),
            chart_count=len(chart_files),
        )
        print("\nDone! 🎉")

    except KeyboardInterrupt:
        logger.info("research_interrupted", topic=topic)
        print("\n⚠️  Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error("research_failed", topic=topic, error=str(e))
        print(f"\n❌ Error: {e}")
        if ENABLE_DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def run_ui():
    """Launch the Streamlit web UI."""
    import subprocess
    ui_path = Path(__file__).parent / "ui" / "streamlit_app.py"

    if not ui_path.exists():
        print(f"❌ UI file not found: {ui_path}")
        sys.exit(1)

    print("🚀 Launching Contelix Web UI...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(ui_path)])


def run_api():
    """Launch the FastAPI server."""
    import subprocess
    print("🚀 Launching Contelix API on http://0.0.0.0:8000 ...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "contelix.api.app:app",
         "--host", "0.0.0.0", "--port", "8000"]
    )


def main():
    """CLI entry point for Contelix."""
    configure_logging()

    parser = argparse.ArgumentParser(
        description="Contelix — AI-Powered Competitive Intelligence Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  contelix research "Tesla EV competitive analysis"
  contelix research "Cloud computing market 2024" --verbose
  contelix research "AI code assistant tools comparison" --output ./reports
  contelix run-ui
  contelix run-api
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # research subcommand
    research_parser = subparsers.add_parser("research", help="Run a research task")
    research_parser.add_argument("topic", help="Research topic or question")
    research_parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory for reports (default: ./output)",
    )
    research_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed agent progress",
    )

    # run-ui subcommand
    subparsers.add_parser("run-ui", help="Launch the Streamlit web UI")

    # run-api subcommand
    subparsers.add_parser("run-api", help="Launch the FastAPI server")

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
