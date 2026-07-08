"""
Data visualization and Python execution tools for generating charts.

Code execution uses a subprocess-based sandbox for security.
"""

from typing import Annotated

from langchain_core.tools import tool

from contelix.config import OUTPUT_DIR
from contelix.tools.sandbox import execute_sandboxed


@tool
def execute_python(
    code: Annotated[str, "Python code to execute. Use print() to see output."],
) -> str:
    """
    Execute Python code to perform data analysis or create visualizations.

    Use this tool to:
    - Analyze collected research data (with pandas, numpy)
    - Create charts and graphs (with matplotlib)
    - Perform calculations and statistical analysis

    Important:
    - Always use print() to display values you want to see.
    - When creating charts, use plt.savefig('filename.png') instead of plt.show().
    - Save chart files to the output directory so they can be included in reports.
    - Only safe modules are available (matplotlib, numpy, pandas, json, etc.).

    Args:
        code: Python code string to execute.

    Returns:
        Standard output from the executed code, or error message if it failed.
    """
    return execute_sandboxed(code)


@tool
def generate_comparison_chart(
    data_json: Annotated[str, "JSON string with chart data. Format: "
                        "{'labels': ['A','B','C'], "
                        "'datasets': [{'label': 'Metric 1', 'values': [1,2,3]}]}"],
    chart_type: Annotated[str, "Chart type: 'bar', 'horizontal_bar', or 'radar'."],
    title: Annotated[str, "Chart title."],
    filename: Annotated[str, "Output filename (e.g., 'comparison.png')."],
) -> str:
    """
    Generate a comparison chart from structured data.

    Use this to create visual competitive comparisons like:
    - Feature comparison bar charts
    - Market share pie charts
    - Competitive positioning radars
    - Trend line charts

    Args:
        data_json: JSON-formatted chart data.
        chart_type: Type of chart ('bar', 'horizontal_bar', 'radar').
        title: Title for the chart.
        filename: Name for the output PNG file.

    Returns:
        Path to the saved chart file, or error message.
    """
    import json
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    try:
        data = json.loads(data_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON data: {e}"

    labels = data.get("labels", [])
    datasets = data.get("datasets", [])

    if not labels or not datasets:
        return "Error: data_json must include 'labels' and 'datasets'."

    fig, ax = plt.subplots(figsize=(10, 6))

    if chart_type == "bar":
        x = np.arange(len(labels))
        width = 0.8 / len(datasets)
        for i, ds in enumerate(datasets):
            ax.bar(x + i * width, ds.get("values", []), width, label=ds.get("label", f"Series {i}"))
        ax.set_xticks(x + width * (len(datasets) - 1) / 2)
        ax.set_xticklabels(labels, rotation=45, ha="right")

    elif chart_type == "horizontal_bar":
        y = np.arange(len(labels))
        height = 0.8 / len(datasets)
        for i, ds in enumerate(datasets):
            ax.barh(y + i * height, ds.get("values", []), height, label=ds.get("label", f"Series {i}"))
        ax.set_yticks(y + height * (len(datasets) - 1) / 2)
        ax.set_yticklabels(labels)

    elif chart_type == "radar":
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle
        ax = fig.add_subplot(111, polar=True)
        for ds in datasets:
            values = ds.get("values", [])
            values += values[:1]
            ax.plot(angles, values, "o-", label=ds.get("label", "Series"))
            ax.fill(angles, values, alpha=0.1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
    else:
        plt.close()
        return f"Unknown chart type: {chart_type}. Use 'bar', 'horizontal_bar', or 'radar'."

    ax.set_title(title)
    ax.legend(loc="best")
    plt.tight_layout()

    filepath = OUTPUT_DIR / filename
    fig.savefig(filepath, dpi=150)
    plt.close(fig)

    return f"Chart saved to {filepath}"
