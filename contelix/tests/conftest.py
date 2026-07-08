"""
Shared test fixtures for Contelix tests.

Provides consistent environment setup, temporary directories,
and mock LLM utilities for all test modules.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    """
    Reset relevant environment variables and set a safe output
    directory for each test. Runs automatically for all tests.
    """
    monkeypatch.setenv("CONTELIX_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("CONTELIX_MODEL_API_KEY", "test-model-key-12345")
    monkeypatch.setenv("BOCHA_API_KEY", "test-bocha-key-67890")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("CONTELIX_CHECKPOINT_BACKEND", "memory")
    monkeypatch.setenv("CONTELIX_SANDBOX_TIMEOUT", "10")

    # Force reload of config to pick up new env vars
    import contelix.config
    # Reset module-level cache
    contelix.config.OUTPUT_DIR = contelix.config.get_output_dir()


@pytest.fixture
def output_dir(clean_env, tmp_path):
    """Return the test output directory."""
    return Path(tmp_path)


@pytest.fixture
def mock_llm():
    """
    Provide a mock LLM that returns predictable responses.

    The mock returns predetermined routing decisions and agent
    responses for deterministic testing of graph logic.
    """
    mock = MagicMock()
    # Default: route to FINISH
    mock.with_structured_output.return_value.invoke.return_value = {
        "next": "FINISH"
    }
    # Default: simple text response
    mock.invoke.return_value = MagicMock(
        content="Mock agent response for testing.",
    )
    return mock
