from utils import *

######################### 设置文件存储路径 ####################################
# _TEMP_DIRECTORY = TemporaryDirectory()
# WORKING_DIRECTORY = Path(_TEMP_DIRECTORY.name)
WORKING_DIRECTORY = Path(os.getcwd()) / "output"
# 确保目录存在
os.makedirs(WORKING_DIRECTORY, exist_ok=True)


######################### 工具定义部分 ####################################
@tool
def create_outline(
    points: Annotated[List[str], "List of main points or sections."],
    file_name: Annotated[str, "File path to save the outline."],
) -> Annotated[str, "Path of the saved outline file."]:
    """
    创建并保存一个大纲
    """
    with (WORKING_DIRECTORY / file_name).open("w") as file:
        for i, point in enumerate(points):
            file.write(f"{i + 1}. {point}\n")
    return f"Outline saved to {file_name}"


# 阅读工具
@tool
def read_document(
    file_name: Annotated[str, "File path to read the document from."],
    start: Annotated[Optional[int], "The start line. Default is 0"] = None,
    end: Annotated[Optional[int], "The end line. Default is None"] = None,
) -> str:
    """阅读指定的文档"""
    with (WORKING_DIRECTORY / file_name).open("r") as file:
        lines = file.readlines()
    if start is None:
        start = 0
    return "\n".join(lines[start:end])


# 写作工具
@tool
def write_document(
    content: Annotated[str, "Text content to be written into the document."],
    file_name: Annotated[str, "File path to save the document."],
) -> Annotated[str, "Path of the saved document file."]:
    """创建并保存文本文档"""
    with (WORKING_DIRECTORY / file_name).open("w") as file:
        file.write(content)
    return f"Document saved to {file_name}"


# 文档编辑工具
@tool
def edit_document(
    file_name: Annotated[str, "Path of the document to be edited."],
    inserts: Annotated[
        Dict[int, str],
        "Dictionary where key is the line number (1-indexed) and value is the text to be inserted at that line.",
    ],
) -> Annotated[str, "Path of the edited document file."]:
    """通过在特定行号插入文本来编辑文档"""

    with (WORKING_DIRECTORY / file_name).open("r") as file:
        lines = file.readlines()

    sorted_inserts = sorted(inserts.items())

    for line_number, text in sorted_inserts:
        if 1 <= line_number <= len(lines) + 1:
            lines.insert(line_number - 1, text + "\n")
        else:
            return f"Error: Line number {line_number} is out of range."

    with (WORKING_DIRECTORY / file_name).open("w") as file:
        file.writelines(lines)

    return f"Document edited and saved to {file_name}"


# python执行工具，在真实环境使用时需要小心。
repl = PythonREPL()


# python执行工具
@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """
    使用该工具进行Python代码的执行。如果要查看某个值的输出，应该使用`print(...)`打印出来。这个是用户可见的。
    """
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return f"Successfully executed:\n\`\`\`python\n{code}\n\`\`\`\nStdout: {result}"



################################# 智能体节点创建 #####################################
# 文档写作智能体
doc_writer_agent = create_react_agent(
    llm,
    tools=[write_document, edit_document, read_document],
    prompt=(
        "你可以基于笔记制作者的大纲来读取、写入和编辑文档。"
        "不要提出后续问题。"
    ),
    debug=DEBUG
)


def doc_writing_node(state: State) -> Command[Literal["supervisor"]]:
    """
    文档写作节点
    """
    result = doc_writer_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="doc_writer")
            ]
        },
        # 所有工作者完成工作后都要返回supervisor节点
        goto="supervisor",
    )


# 笔记记录智能体
note_taking_agent = create_react_agent(
    llm,
    tools=[create_outline, read_document],
    prompt=(
        "你可以阅读文档并为文档写作者创建大纲。"
        "不要提出后续问题。"
    ),
    debug=DEBUG
)


def note_taking_node(state: State) -> Command[Literal["supervisor"]]:
    """
    笔记制作节点
    """
    result = note_taking_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="note_taker")
            ]
        },
        # 所有工作者完成工作后都要返回supervisor节点
        goto="supervisor",
    )


# 图表生成智能体
chart_generating_agent = create_react_agent(
    llm,
    tools=[read_document, python_repl_tool],
    debug=DEBUG
)


def chart_generating_node(state: State) -> Command[Literal["supervisor"]]:
    """
    图表生成节点
    """
    result = chart_generating_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=result["messages"][-1].content, name="chart_generator"
                )
            ]
        },
        # 所有工作者完成工作后都要返回supervisor节点
        goto="supervisor",
    )


# 文档写作团队主控节点
doc_writing_supervisor_node = make_supervisor_node(
    llm, ["doc_writer", "note_taker", "chart_generator"]
)


############################### 图模式构造 ###################################
paper_writing_builder = StateGraph(State)
paper_writing_builder.add_node("supervisor", doc_writing_supervisor_node)
paper_writing_builder.add_node("doc_writer", doc_writing_node)
paper_writing_builder.add_node("note_taker", note_taking_node)
paper_writing_builder.add_node("chart_generator", chart_generating_node)

paper_writing_builder.add_edge(START, "supervisor")
paper_writing_graph = paper_writing_builder.compile()


