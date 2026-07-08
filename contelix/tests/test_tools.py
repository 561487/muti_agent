"""
Unit tests for Contelix tools.
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from contelix.tools.file_ops import create_outline, write_document, read_document, edit_document, list_output_files


class TestFileOps:
    """Test file operation tools."""

    def test_write_and_read_document(self, tmp_path):
        """Test basic write and read operations."""
        import os
        os.environ["CONTELIX_OUTPUT_DIR"] = str(tmp_path)

        result = write_document.invoke({
            "content": "# Test Report\n\nHello World!",
            "file_name": "test.md",
        })
        assert "successfully" in result.lower()

        content = read_document.invoke({"file_name": "test.md"})
        assert "Hello World!" in content

    def test_create_outline(self, tmp_path):
        """Test outline creation."""
        import os
        os.environ["CONTELIX_OUTPUT_DIR"] = str(tmp_path)

        result = create_outline.invoke({
            "points": ["Introduction", "Analysis", "Conclusion"],
            "file_name": "outline.txt",
        })
        assert "saved" in result.lower()

        content = read_document.invoke({"file_name": "outline.txt"})
        assert "1. Introduction" in content
        assert "2. Analysis" in content
        assert "3. Conclusion" in content

    def test_edit_document(self, tmp_path):
        """Test document editing with line inserts."""
        import os
        os.environ["CONTELIX_OUTPUT_DIR"] = str(tmp_path)

        write_document.invoke({
            "content": "Line 1\nLine 2\nLine 4\n",
            "file_name": "edit_test.md",
        })

        result = edit_document.invoke({
            "file_name": "edit_test.md",
            "inserts": {3: "Line 3 (inserted)"},
        })
        assert "edited" in result.lower()

        content = read_document.invoke({"file_name": "edit_test.md"})
        assert "Line 3 (inserted)" in content

    def test_list_output_files(self, tmp_path):
        """Test listing output files."""
        import os
        os.environ["CONTELIX_OUTPUT_DIR"] = str(tmp_path)

        write_document.invoke({"content": "test", "file_name": "a.md"})
        write_document.invoke({"content": "test", "file_name": "b.md"})

        result = list_output_files.invoke({})
        assert "a.md" in result
        assert "b.md" in result

    def test_read_nonexistent_file(self, tmp_path):
        """Test reading a file that doesn't exist."""
        import os
        os.environ["CONTELIX_OUTPUT_DIR"] = str(tmp_path)

        result = read_document.invoke({"file_name": "ghost.md"})
        assert "not found" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
