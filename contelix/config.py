"""
Contelix Configuration Management.

All secrets and model settings are read from environment variables.
Copy .env.example to .env and fill in your API keys.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root or current directory
load_dotenv(PROJECT_ROOT / ".env")

# ── Project Paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
OUTPUT_DIR = Path(os.getenv("CONTELIX_OUTPUT_DIR", PROJECT_ROOT / "output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── LLM Configuration ──────────────────────────────────────────────────────
MODEL_NAME = os.getenv("CONTELIX_MODEL_NAME", "qwen2.5-72b-instruct")
MODEL_BASE_URL = os.getenv(
    "CONTELIX_MODEL_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
MODEL_API_KEY = os.getenv("CONTELIX_MODEL_API_KEY", "")
MODEL_TEMPERATURE = float(os.getenv("CONTELIX_MODEL_TEMPERATURE", "0"))

# ── Search API Configuration ──────────────────────────────────────────────
BOCHA_API_KEY = os.getenv("BOCHA_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# If Tavily key is set, set it for the langchain_community library
if TAVILY_API_KEY:
    os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

# ── Runtime Configuration ──────────────────────────────────────────────────
MAX_RECURSION_LIMIT = int(os.getenv("CONTELIX_MAX_RECURSION", "150"))
ENABLE_DEBUG = os.getenv("CONTELIX_DEBUG", "false").lower() == "true"

# ── Checkpoint / Persistence ────────────────────────────────────────────────
CHECKPOINT_BACKEND = os.getenv("CONTELIX_CHECKPOINT_BACKEND", "memory")
"""Checkpoint backend: 'memory', 'sqlite', or 'postgres'."""
CHECKPOINT_DB_PATH = os.getenv("CONTELIX_CHECKPOINT_DB_PATH", "contelix_checkpoints.db")
"""Database path or connection string for checkpoint persistence."""

# ── LangSmith Observability ──────────────────────────────────────────────────
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "contelix")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

# Set LangSmith env vars before any LangChain imports
if LANGSMITH_TRACING and LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT

# ── Sandbox ──────────────────────────────────────────────────────────────────
SANDBOX_TIMEOUT = int(os.getenv("CONTELIX_SANDBOX_TIMEOUT", "30"))
"""Maximum execution time in seconds for sandboxed Python code."""

# ── Visualization ──────────────────────────────────────────────────────────
os.environ["MPLBACKEND"] = "Agg"  # Non-interactive matplotlib backend


def get_output_dir() -> Path:
    """Return the current output directory, creating it if needed."""
    out = Path(os.getenv("CONTELIX_OUTPUT_DIR", PROJECT_ROOT / "output"))
    out.mkdir(parents=True, exist_ok=True)
    return out


def create_task_dir(topic: str) -> Path:
    """为研究任务创建独立的输出子目录。

    目录名格式: <话题前30字符>_<时间戳>

    Args:
        topic: 研究话题，用于生成目录名。

    Returns:
        创建好的任务输出目录路径。
    """
    import re
    from datetime import datetime
    safe = re.sub(r'[\\/*?:"<>|]', '', topic)[:30].strip()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_dir = get_output_dir() / f"{safe}_{ts}"
    task_dir.mkdir(parents=True, exist_ok=True)
    os.environ["CONTELIX_OUTPUT_DIR"] = str(task_dir)
    return task_dir


def validate_config() -> bool:
    """Validate that required configuration is present."""
    missing = []
    if not MODEL_API_KEY:
        missing.append("CONTELIX_MODEL_API_KEY")
    if not BOCHA_API_KEY and not TAVILY_API_KEY:
        missing.append("BOCHA_API_KEY or TAVILY_API_KEY")

    if missing:
        print(f"⚠  Missing required environment variables: {', '.join(missing)}")
        print("  Copy .env.example to .env and fill in your API keys.")
        return False
    return True


def print_config():
    """Print current configuration (masking secrets)."""
    print(f"Model: {MODEL_NAME}")
    print(f"Model Base URL: {MODEL_BASE_URL}")
    print(f"Model API Key: {'***' + MODEL_API_KEY[-4:] if MODEL_API_KEY else 'NOT SET'}")
    print(f"Bocha API Key: {'***' + BOCHA_API_KEY[-4:] if BOCHA_API_KEY else 'NOT SET'}")
    print(f"Tavily API Key: {'***' + TAVILY_API_KEY[-4:] if TAVILY_API_KEY else 'NOT SET'}")
    print(f"Output Dir: {OUTPUT_DIR}")
    print(f"Debug: {ENABLE_DEBUG}")
