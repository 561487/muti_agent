import time
import io

from PIL import Image
from typing import Annotated
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START
from typing import Literal
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from config import MODEL_API_KEY, MODEL_BASE_URL, MODEL

DEBUG = True
SUBGRAPH = False

######################### 工具与模型定义部分 ####################################
llm = ChatOpenAI(
    model=MODEL,
    base_url=MODEL_BASE_URL,
    api_key=MODEL_API_KEY,
    temperature=0
)

# 信息搜索工具 https://app.tavily.com/home
tavily_tool = TavilySearchResults(max_results=5)

# python执行工具，在真实环境使用时需要小心。
repl = PythonREPL()


@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """使用该工具进行Python代码的执行。如果要查看某个值的输出，应该使用`print(...)`打印出来。这个是用户可见的。"""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n\`\`\`python\n{code}\n\`\`\`\nStdout: {result}"
    time.sleep(1)

    return (
        result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."
    )


def make_system_prompt(suffix: str) -> str:
    return (
        "你是一个乐于助人的 AI 助手，可以与其他助手合作。"
        "你可以使用提供的工具来逐步回答问题。"
        "如果无法完全回答，没关系，其他拥有不同工具的助手会在你停止的地方继续帮助。"
        "尽你所能取得进展。如果你或其他助手有最终答案或成果，请在回复前加上FINAL ANSWER，以便团队知道可以停止了。"
        f"\n{suffix}"
    )


def get_next_node(last_message: BaseMessage, goto: str):
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return END
    return goto


# Research agent and node
research_agent = create_react_agent(
    llm,
    tools=[tavily_tool],
    prompt=make_system_prompt(
        "你只能做研究工作。你和一位图表生成器同事一起工作。"
    ),
    debug=DEBUG
)


def research_node(
    state: MessagesState,
) -> Command[Literal["chart_generator", END]]:
    result = research_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "chart_generator")
    # wrap in a human message, as not all providers allow
    # AI message at the last position of the input messages list
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="researcher"
    )
    return Command(
        update={
            # 与其他agent共享研究代理的内部消息记录
            "messages": result["messages"],
        },
        goto=goto,
    )


# 图表生成器agent和节点
# 注意：这会执行任意代码，若未进行沙盒隔离，则可能存在安全隐患。
chart_agent = create_react_agent(
    llm,
    [python_repl_tool],
    prompt=make_system_prompt(
        "你是一位专注于数据可视化的程序员。"
        "您的工作是使用 Python 代码创建图表和可视化内容。"
        "可以使用 matplotlib、pandas 或其他合适的库。"
        "在处理数据时，要创建高质量的可视化内容。"
        "不要使用 plt.show() 来展示可视化内容，而要始终使用 plt.savefig('filename.png') 将其保存到文件中，以便在非交互式环境中正确查看。",
    ),
    debug=DEBUG
)


def chart_node(state: MessagesState) -> Command[Literal["researcher", END]]:
    result = chart_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "researcher")
    # 包装成humanMessage，因为并非所有模型都允许AIMessage位于输入消息列表的最后位置
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="chart_generator"
    )
    return Command(
        update={
            # 与其他agent共享图表agent的内部消息记录
            "messages": result["messages"],
        },
        goto=goto,
    )


############################### 图模式构造 ###################################
workflow = StateGraph(MessagesState)
workflow.add_node("researcher", research_node)
workflow.add_node("chart_generator", chart_node)
workflow.add_edge(START, "researcher")
graph = workflow.compile()

# img = graph.get_graph().draw_mermaid_png()
# image = Image.open(io.BytesIO(img))
# image.save("./network.png")


def network_example():
    for s in graph.stream(
        {
            "messages": [
                (
                    "user",
                    "首先，获取英国过去5年的国内生产总值（GDP），然后绘制其折线图。绘制完图表后，就完成了。",
                )
            ],
        },
        # Maximum number of steps to take in the graph
        {"recursion_limit": 150},
        subgraphs=SUBGRAPH
    ):
        print(s)
        print("----")


network_example()

