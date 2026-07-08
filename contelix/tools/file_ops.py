"""
File operation tools for report writing, editing, and management.
"""

from pathlib import Path
from typing import Annotated, Dict, List, Optional

from langchain_core.tools import tool

from contelix.config import get_output_dir


def _resolve_safe_path(file_name: str) -> Path:
    """
    Resolve a file path relative to OUTPUT_DIR with path-traversal protection.

    Ensures the resolved path stays within OUTPUT_DIR. Raises ValueError if
    the path attempts to escape via ``..`` segments or absolute paths.

    Args:
        file_name: File name or relative path within OUTPUT_DIR.

    Returns:
        Resolved absolute Path within OUTPUT_DIR.

    Raises:
        ValueError: If the resolved path escapes OUTPUT_DIR.
    """
    output = get_output_dir().resolve()
    target = (output / file_name).resolve()

    # Check that target is OUTPUT_DIR itself or a child of it
    if output not in target.parents and target != output:
        raise ValueError(
            f"Path traversal rejected: '{file_name}' resolves outside "
            f"the output directory."
        )
    return target


@tool
def create_outline(
    points: Annotated[List[str], "List of main points or sections for the outline."],
    file_name: Annotated[str, "File path to save the outline (relative to output dir)."],
) -> str:
    """
    Create and save a document outline.

    Use this to create a structured outline before writing a full report.
    Each point in the list becomes a numbered section.

    Args:
        points: List of section titles or main points.
        file_name: Name of the outline file (e.g., 'outline.txt').

    Returns:
        Confirmation message with the file path.
    """
    file_path = _resolve_safe_path(file_name)
    with open(file_path, "w") as f:
        for i, point in enumerate(points, 1):
            f.write(f"{i}. {point}\n")
    return f"Outline with {len(points)} sections saved to {file_path}"


@tool
def read_document(
    file_name: Annotated[str, "File path to read (relative to output dir)."],
    start: Annotated[Optional[int], "Starting line number (0-indexed, default 0)."] = None,
    end: Annotated[Optional[int], "Ending line number (exclusive, default None = all)."] = None,
) -> str:
    """
    Read the contents of a document from the output directory.

    Use this to review what has been written so far before editing or continuing.

    Args:
        file_name: Name of the file to read.
        start: First line to read (0-indexed). Defaults to beginning.
        end: Last line to read (exclusive). Defaults to end of file.

    Returns:
        The document contents as a string.
    """
    file_path = _resolve_safe_path(file_name)
    if not file_path.exists():
        return f"File not found: {file_path}"

    with open(file_path, "r") as f:
        lines = f.readlines()

    if start is None:
        start = 0
    return "".join(lines[start:end])


@tool
def write_document(
    content: Annotated[str, "Full text content to write to the document."],
    file_name: Annotated[str, "File name to save the document as."],
) -> str:
    """
    Create or overwrite a document with new content.

    Use this to write a complete document such as a research report,
    analysis summary, or competitive brief.

    Args:
        content: The complete text content of the document.
        file_name: Name of the file (e.g., 'tesla_analysis_report.md').

    Returns:
        Confirmation message with the file path.
    """
    file_path = _resolve_safe_path(file_name)
    with open(file_path, "w") as f:
        f.write(content)
    return f"Document written successfully to {file_path} ({len(content)} characters)"


@tool
def edit_document(
    file_name: Annotated[str, "Path of the document to edit (relative to output dir)."],
    inserts: Annotated[
        Dict[int, str],
        "Dictionary mapping line numbers (1-indexed) to text to insert at that line.",
    ],
) -> str:
    """
    Insert text at specific line numbers in an existing document.

    Use this to add or update sections in a report without rewriting the entire file.
    Line numbers are 1-indexed (first line is line 1).

    Args:
        file_name: Name of the file to edit.
        inserts: Dict where key=line number, value=text to insert.

    Returns:
        Confirmation message.
    """
    file_path = _resolve_safe_path(file_name)
    if not file_path.exists():
        return f"File not found: {file_path}. Use write_document to create it first."

    with open(file_path, "r") as f:
        lines = f.readlines()

    sorted_inserts = sorted(inserts.items())
    for line_number, text in sorted_inserts:
        if 1 <= line_number <= len(lines) + 1:
            lines.insert(line_number - 1, text + "\n")
        else:
            return f"Error: Line number {line_number} is out of range (1-{len(lines)+1})."

    with open(file_path, "w") as f:
        f.writelines(lines)

    return f"Document edited: {len(sorted_inserts)} insertions made to {file_path}"


@tool
def list_output_files() -> str:
    """
    List all files currently in the output directory.

    Use this to check what reports and documents have been created.

    Returns:
        Listing of all output files with sizes.
    """
    files = sorted(get_output_dir().glob("*"))
    if not files:
        return "No files in output directory."

    lines = []
    for f in files:
        if f.is_file():
            size_kb = f.stat().st_size / 1024
            lines.append(f"  {f.name} ({size_kb:.1f} KB)")
    return "Files in output directory:\n" + "\n".join(lines) if lines else "No files found."
