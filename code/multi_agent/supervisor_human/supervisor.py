from typing import Annotated

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from typing import Literal
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, END
from langgraph.types import Command, interrupt
from config import MODEL_API_KEY, MODEL_BASE_URL, MODEL

DEBUG = False
SUBGRAPH = False

######################### 工具与模型定义部分 ####################################
llm = ChatOpenAI(
    model=MODEL,
    base_url=MODEL_BASE_URL,
    api_key=MODEL_API_KEY,
    temperature=0
)

# 信息搜索工具
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
    return result_str


################################# 智能体节点创建 #####################################
members = ["researcher", "coder"]

system_prompt = (
    f"你是一名主管，负责管理以下工作者之间的对话：{members}。"
    "对于给定的用户请求，和你的工作者一起回应下一步的行动"
    "考虑到以下用户请求，和工作者一起回应下一步的行动。每个工作者将执行一个任务并且回应他们执行的结果和状态。"
    "重要：研究人员负责查找信息和收集数据。"
    "程序员负责使用Python代码创建图表和可视化。"
    "当用户的请求涉及研究员和程序员任务时，首先路由到研究人员去收集数据，然后到程序员去创建数据的可视化。"
    "只有在两个任务都完成时才回应FINISH。"
)


class Router(TypedDict):
    """下一个路由的工作节点。如果不需要额外的工作节点，则路由到FINISH。"""

    next: Literal["researcher", "coder", "FINISH"]


class State(MessagesState):
    next: str


def supervisor_node(state: State):
    """主控智能体由大模型构成，决策具体执行节点是哪个"""
    messages = [{"role": "system", "content": system_prompt},] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    print(f"Supervisor decision: {goto}")

    if goto == "coder":
        human_review = interrupt(
            {
                "question": "是否允许进行代码执行",
            }
        )
        print(f"用户返回为{human_review}")
        if human_review:
            return Command(goto=goto, update={"next": goto})
        else:
            return Command(goto="FINISH", update={"next": goto})
    if goto == "FINISH":
        goto = END

    return Command(goto=goto, update={"next": goto})


# 研究员agent
research_agent = create_react_agent(
    llm,
    tools=[tavily_tool],
    prompt="你是一名研究人员，你的工作是查找信息和收集数据。你应该专注于寻找准确且最新的信息。",
    debug=DEBUG
)


def research_node(state: State) -> Command[Literal["supervisor"]]:
    print("Entering research node")
    result = research_agent.invoke(state)
    print(f"Research agent result: {result['messages'][-1].content[:100]}...")
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="researcher")
            ]
        },
        goto="supervisor",
    )


# 注意：这会执行任意代码，若未进行沙盒隔离，则可能存在安全隐患。
code_agent = create_react_agent(
    llm,
    tools=[python_repl_tool],
    prompt="你是一位专注于数据可视化的程序员。"
           "您的工作是使用 Python 代码创建图表和可视化内容。"
           "可以使用 matplotlib、pandas 或其他合适的库。"
           "在处理数据时，要创建高质量的可视化内容。"
           "不要使用 plt.show() 来展示可视化内容，而要始终使用 plt.savefig('filename.png') 将其保存到文件中，以便在非交互式环境中正确查看。",
    debug=DEBUG
)


def code_node(state: State) -> Command[Literal["supervisor"]]:
    print("Entering code node")
    result = code_agent.invoke(state)
    print(f"Code agent result: {result['messages'][-1].content[:100]}...")
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="coder")
            ]
        },
        goto="supervisor",
    )

############################### 图模式构造 ###################################
builder = StateGraph(State)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", research_node)
builder.add_node("coder", code_node)

checkpoint = MemorySaver()
graph = builder.compile(checkpointer=checkpoint)

# for s in graph.stream({"messages": [("user", "What's the square root of 42?")]}):
#     print(s)
#     print("----")


def supervisor_example():
    """
    supervisor图模式运行实例
    """
    thread_config = {"configurable": {"thread_id": "1"}}
    for s in graph.stream(
            {
                "messages": [
                    (
                        "user",
                        "首先，获取英国过去5年的国内生产总值（GDP），然后绘制其折线图。绘制完图表后，就完成了。"
                    )
                ],
                "next": ""
            },
            config=thread_config,
            subgraphs=SUBGRAPH
    ):
        print(s)
        print("----")

    for s in graph.stream(Command(resume=True), config=thread_config):
        print(s)
        print("------------")

supervisor_example()



