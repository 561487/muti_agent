"""Unit tests for visualization tools and sandbox."""

import json

import pytest

from contelix.tools.visualization import generate_comparison_chart, execute_python
from contelix.tools.sandbox import execute_sandboxed


class TestGenerateComparisonChart:
    """Tests for generate_comparison_chart tool."""

    def test_bar_chart(self, output_dir, monkeypatch):
        """Should generate a bar chart PNG file."""
        import contelix.config
        # Patch get_output_dir to return the test temp dir
        monkeypatch.setattr(contelix.config, "get_output_dir", lambda: output_dir)

        data = json.dumps({
            "labels": ["Company A", "Company B", "Company C"],
            "datasets": [
                {"label": "Revenue", "values": [100, 150, 80]},
            ],
        })
        result = generate_comparison_chart.invoke({
            "data_json": data,
            "chart_type": "bar",
            "title": "Revenue Comparison",
            "filename": "test_bar.png",
        })
        assert "saved" in result.lower()
        assert (output_dir / "test_bar.png").exists()

    def test_horizontal_bar_chart(self, output_dir):
        """Should generate a horizontal bar chart."""
        data = json.dumps({
            "labels": ["Feature X", "Feature Y"],
            "datasets": [
                {"label": "Score", "values": [8, 6]},
            ],
        })
        result = generate_comparison_chart.invoke({
            "data_json": data,
            "chart_type": "horizontal_bar",
            "title": "Feature Scores",
            "filename": "test_hbar.png",
        })
        assert "saved" in result.lower()

    def test_invalid_json(self):
        """Should return error for invalid JSON data."""
        result = generate_comparison_chart.invoke({
            "data_json": "not valid json",
            "chart_type": "bar",
            "title": "Test",
            "filename": "test.png",
        })
        assert "Invalid" in result or "Error" in result

    def test_unknown_chart_type(self):
        """Should return error for unknown chart type."""
        data = json.dumps({"labels": ["A"], "datasets": [{"label": "X", "values": [1]}]})
        result = generate_comparison_chart.invoke({
            "data_json": data,
            "chart_type": "scatter",
            "title": "Test",
            "filename": "test.png",
        })
        assert "Unknown" in result


class TestSandbox:
    """Security tests for the sandboxed Python execution."""

    def test_safe_code_executes(self):
        """Safe code should execute successfully."""
        result = execute_sandboxed("print(1 + 1)")
        assert "2" in result

    def test_math_import_allowed(self):
        """Allowed modules should be importable."""
        result = execute_sandboxed("import math\nprint(f'sqrt(16)={math.sqrt(16)}')")
        assert "4.0" in result

    def test_os_import_blocked(self):
        """os module import should be blocked."""
        result = execute_sandboxed("import os\nprint(os.getcwd())")
        assert "not allowed" in result.lower() or "error" in result.lower()

    def test_path_traversal_blocked(self):
        """Absolute file paths should be blocked."""
        result = execute_sandboxed("open('/etc/passwd').read()")
        assert "denied" in result.lower() or "error" in result.lower()
