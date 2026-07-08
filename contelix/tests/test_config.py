"""Unit tests for configuration management."""

import os

import pytest

from contelix.config import (
    validate_config,
    get_output_dir,
    OUTPUT_DIR,
    MODEL_NAME,
    MAX_RECURSION_LIMIT,
    SANDBOX_TIMEOUT,
)


class TestValidateConfig:
    """Tests for validate_config()."""

    def test_missing_model_key(self, clean_env, monkeypatch):
        """Should return False when MODEL_API_KEY is empty."""
        import contelix.config
        monkeypatch.setattr(contelix.config, "MODEL_API_KEY", "")
        monkeypatch.setattr(contelix.config, "BOCHA_API_KEY", "")
        monkeypatch.setattr(contelix.config, "TAVILY_API_KEY", "")
        assert contelix.config.validate_config() is False

    def test_missing_search_key(self, clean_env, monkeypatch):
        """Should return False when no search key is configured."""
        import contelix.config
        monkeypatch.setattr(contelix.config, "MODEL_API_KEY", "sk-test")
        monkeypatch.setattr(contelix.config, "BOCHA_API_KEY", "")
        monkeypatch.setattr(contelix.config, "TAVILY_API_KEY", "")
        assert contelix.config.validate_config() is False

    def test_valid_config(self, clean_env, monkeypatch):
        """Should return True when all required keys are set."""
        import contelix.config
        monkeypatch.setattr(contelix.config, "MODEL_API_KEY", "sk-test")
        monkeypatch.setattr(contelix.config, "BOCHA_API_KEY", "sk-test")
        assert contelix.config.validate_config() is True

    def test_valid_with_tavily_only(self, clean_env, monkeypatch):
        """Should return True with just Tavily API key."""
        import contelix.config
        monkeypatch.setattr(contelix.config, "MODEL_API_KEY", "sk-test")
        monkeypatch.setattr(contelix.config, "BOCHA_API_KEY", "")
        monkeypatch.setattr(contelix.config, "TAVILY_API_KEY", "tvly-test")
        assert contelix.config.validate_config() is True


class TestGetOutputDir:
    """Tests for get_output_dir()."""

    def test_default_output_dir(self, clean_env, tmp_path):
        """Should return env-configured output directory."""
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setenv("CONTELIX_OUTPUT_DIR", str(tmp_path / "reports"))
        import contelix.config
        output = contelix.config.get_output_dir()
        assert output == tmp_path / "reports"
        assert output.exists()

    def test_creates_directory(self, clean_env, tmp_path):
        """Should create the output directory if it doesn't exist."""
        new_dir = tmp_path / "new_output"
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setenv("CONTELIX_OUTPUT_DIR", str(new_dir))
        import contelix.config
        output = contelix.config.get_output_dir()
        assert output.exists()


class TestDefaults:
    """Tests for default configuration values."""

    def test_default_model_name(self):
        """Should have a default model name."""
        assert MODEL_NAME is not None
        assert len(MODEL_NAME) > 0

    def test_default_recursion_limit(self):
        """Should have a reasonable recursion limit."""
        assert MAX_RECURSION_LIMIT >= 50

    def test_default_sandbox_timeout(self):
        """Should have a positive sandbox timeout."""
        assert SANDBOX_TIMEOUT > 0
