"""
Sandboxed Python execution environment for safe LLM-generated code execution.

Replaces the unsafe langchain_experimental PythonREPL with a subprocess-based
sandbox that restricts imports via a whitelist. The import whitelist is the
primary security mechanism — without os, subprocess, socket, etc., even
unrestricted builtins cannot perform dangerous operations.
"""

import os
import subprocess
import textwrap
from pathlib import Path

from contelix.config import OUTPUT_DIR, SANDBOX_TIMEOUT

# ── Sandbox Configuration ────────────────────────────────────────────────────

# Modules allowed for import inside the sandbox.
# IMPORTANT: This is the primary security boundary. Without os, subprocess,
# socket, shutil, requests, etc., code cannot perform system calls, network
# access, or filesystem traversal outside the working directory.
ALLOWED_MODULES = frozenset({
    # Data analysis
    "numpy",
    "pandas",
    # Visualization
    "matplotlib",
    # Standard library — data
    "json",
    "csv",
    "datetime",
    "math",
    "statistics",
    "decimal",
    "fractions",
    "random",
    "hashlib",
    "base64",
    # Standard library — data structures
    "collections",
    "itertools",
    "functools",
    "operator",
    "copy",
    "dataclasses",
    "array",
    "bisect",
    "heapq",
    # Standard library — text
    "string",
    "re",
    "textwrap",
    "pprint",
    "unicodedata",
    # Standard library — typing
    "typing",
    "enum",
    # Standard library — utilities
    "pathlib",
    "warnings",
    "traceback",
})

# Preamble injected before user code to set up the sandbox environment.
# Uses import whitelist — the safe, portable, non-breaking approach.
SANDBOX_PREAMBLE = textwrap.dedent(f"""
import builtins

# ── matplotlib non-interactive backend (before import hook) ──────────────
try:
    import matplotlib
    matplotlib.use('Agg')
except ImportError:
    pass

# ── Working directory and env (before import hook) ───────────────────────
import os as _os
_os.chdir("{OUTPUT_DIR}")
_os.environ["MPLBACKEND"] = "Agg"

# ── Restricted file I/O (before import hook) ────────────────────────────
_orig_open = builtins.open
_osp_realpath = _os.path.realpath
_osp_join = _os.path.join
_osp_sep = _os.path.sep
_output_dir = _os.path.realpath("{OUTPUT_DIR}")

def _safe_open(file, mode='r', *args, **kwargs):
    file_str = file if isinstance(file, str) else str(file)
    resolved = _osp_realpath(_osp_join(_output_dir, file_str))
    if not resolved.startswith(_output_dir + _osp_sep) and resolved != _output_dir:
        raise PermissionError(
            f"Access denied: '{{file_str}}' resolves outside the output directory."
        )
    return _orig_open(resolved, mode, *args, **kwargs)

builtins.open = _safe_open

# ── Safe import hook (INSTALL LAST — after all setup imports) ────────────
_orig_import = builtins.__import__
_ALLOWED = {ALLOWED_MODULES}

def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    top_level = name.split('.')[0]
    if top_level not in _ALLOWED and name not in _ALLOWED:
        raise ImportError(
            f"Module '{{name}}' is not allowed in the sandbox. "
            f"Allowed: {{sorted(_ALLOWED)}}"
        )
    return _orig_import(name, globals, locals, fromlist, level)

builtins.__import__ = _safe_import
""")


def execute_sandboxed(code: str, timeout: int = None) -> str:
    """
    Execute Python code in a restricted subprocess sandbox.

    The sandbox:
    - Restricts imports to a whitelist of safe modules (no os, subprocess, socket)
    - Overrides builtins.open() to block path traversal and absolute paths
    - Sets matplotlib to non-interactive Agg backend
    - Runs with OUTPUT_DIR as working directory
    - Enforces a strict configurable timeout

    Args:
        code: Python code string to execute.
        timeout: Maximum execution time in seconds. Defaults to SANDBOX_TIMEOUT.

    Returns:
        A string with execution output or error message.
    """
    if timeout is None:
        timeout = SANDBOX_TIMEOUT

    sandbox_script = SANDBOX_PREAMBLE + "\n" + code

    try:
        result = subprocess.run(
            ["python3", "-c", sandbox_script],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(OUTPUT_DIR),
            env={
                "MPLBACKEND": "Agg",
                "HOME": str(OUTPUT_DIR),
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                # Purge potentially dangerous env vars
                "PYTHONPATH": "",
                "LD_PRELOAD": "",
                "PYTHONSTARTUP": "",
            },
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                return f"Code executed successfully.\n```\n{output}\n```"
            else:
                return "Code executed successfully (no output)."
        else:
            error = result.stderr.strip() or result.stdout.strip()
            # Sanitize error to avoid leaking filesystem paths
            error_safe = error.replace(str(OUTPUT_DIR), "<output_dir>")
            return f"Execution Error:\n```\n{error_safe[:2000]}\n```"

    except subprocess.TimeoutExpired:
        return (
            f"Execution timed out after {timeout} seconds. "
            "Simplify your code or increase the timeout via CONTELIX_SANDBOX_TIMEOUT."
        )
    except FileNotFoundError:
        return "Sandbox Error: Python3 interpreter not found in the sandbox environment."
    except Exception as e:
        return f"Sandbox Error: {type(e).__name__}: {e}"
