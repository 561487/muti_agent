"""
Contelix FastAPI Application — REST API for competitive intelligence research.

Start with:
    uvicorn contelix.api.app:app --host 0.0.0.0 --port 8000
    or: contelix run-api
"""

import os
import threading
import uuid
import traceback
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import structlog

from contelix.config import (
    validate_config,
    get_output_dir,
    MAX_RECURSION_LIMIT,
    ENABLE_DEBUG,
)
from contelix.agents.supervisor import build_top_graph

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Contelix API",
    version="0.2.0",
    description="AI-Powered Competitive Intelligence Automation Platform",
)

# ── In-memory task store ────────────────────────────────────────────────────
_tasks: dict[str, dict] = {}
_tasks_lock = threading.Lock()


# ── Request/Response Models ──────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    topic: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Research topic, company, or industry question",
    )
    output_dir: Optional[str] = Field(
        None,
        description="Custom output directory for reports",
    )
    verbose: bool = Field(
        False,
        description="Return detailed agent-level output",
    )


class ResearchResponse(BaseModel):
    task_id: str
    status: str
    topic: str
    output_dir: str


class ResearchResult(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    topic: str
    output_dir: str
    report_files: list[str] = []
    chart_files: list[str] = []
    error: Optional[str] = None


# ── Background Task Runner ──────────────────────────────────────────────────

def _run_research_task(task_id: str, request: ResearchRequest):
    """Execute a research task in the background."""
    with _tasks_lock:
        task = _tasks.get(task_id)
        if task is None:
            return
        task["status"] = "running"

    if request.output_dir:
        os.environ["CONTELIX_OUTPUT_DIR"] = str(Path(request.output_dir).resolve())

    output_path = get_output_dir()
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(
        "api.research_started",
        task_id=task_id,
        topic=request.topic,
        output_dir=str(output_path),
    )

    try:
        graph = build_top_graph()
        config = {"recursion_limit": MAX_RECURSION_LIMIT}

        for _ in graph.stream(
            {"topic": request.topic, "messages": [{"role": "user", "content": request.topic}]},
            config,
            subgraphs=True,
        ):
            pass  # Events consumed; results are on disk

        # Collect generated files
        report_files = sorted(
            [f.name for f in output_path.glob("*.md")]
        )
        chart_files = sorted(
            [f.name for f in output_path.glob("*.png")]
        )

        with _tasks_lock:
            task["status"] = "completed"
            task["report_files"] = report_files
            task["chart_files"] = chart_files

        logger.info(
            "api.research_completed",
            task_id=task_id,
            report_count=len(report_files),
            chart_count=len(chart_files),
        )

    except Exception as e:
        with _tasks_lock:
            task["status"] = "failed"
            task["error"] = str(e)
        logger.error(
            "api.research_failed",
            task_id=task_id,
            error=str(e),
        )
        if ENABLE_DEBUG:
            traceback.print_exc()


# ── API Endpoints ───────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    api_keys_ok = validate_config()
    return {
        "status": "healthy",
        "version": "0.2.0",
        "api_configured": api_keys_ok,
    }


@app.post("/research", response_model=ResearchResponse, status_code=202)
async def start_research(request: ResearchRequest):
    """
    Submit a competitive intelligence research task.

    The task runs asynchronously. Use GET /research/{task_id}
    to poll for results.
    """
    if not validate_config():
        raise HTTPException(
            status_code=503,
            detail="API keys not configured. Set CONTELIX_MODEL_API_KEY and search keys.",
        )

    task_id = str(uuid.uuid4())[:8]
    with _tasks_lock:
        _tasks[task_id] = {
            "status": "pending",
            "topic": request.topic,
            "output_dir": str(get_output_dir()),
        }

    thread = threading.Thread(
        target=_run_research_task,
        args=(task_id, request),
        daemon=True,
    )
    thread.start()

    return ResearchResponse(
        task_id=task_id,
        status="pending",
        topic=request.topic,
        output_dir=str(get_output_dir()),
    )


@app.get("/research/{task_id}", response_model=ResearchResult)
async def get_research_result(task_id: str):
    """Get the status and results of a research task."""
    with _tasks_lock:
        if task_id not in _tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        task = dict(_tasks[task_id])  # Snapshot under lock

    return ResearchResult(
        task_id=task_id,
        status=task["status"],
        topic=task.get("topic", ""),
        output_dir=task.get("output_dir", ""),
        report_files=task.get("report_files", []),
        chart_files=task.get("chart_files", []),
        error=task.get("error"),
    )
