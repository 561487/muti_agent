import io

from langchain_core.messages import ToolMessage, AIMessage
from typing import Literal
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict, Annotated
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool, InjectedToolCallId
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from PIL import Image
from config import *


##########################工具及模型构建###################################
@tool
def lookup_user_info(tool_call_id: Annotated[str, InjectedToolCallId], user_name):
    """
    使用该函数查询用户信息以便更好的帮助他们解决问题。

    arg: 用户名称
    """
    return Command(
        update={
            # 修改信息历史
            "messages": [ToolMessage(
                f"Successfully looked up {user_name} information",
                tool_call_id=tool_call_id
            )],
        },
        goto="my_other_node"
    )


tools = [lookup_user_info]
tool_node = ToolNode(tools)
llm = ChatOpenAI(
    model=MODEL,
    base_url=BASE_URL,
    api_key=API_KEY
).bind_tools(tools)


##########################节点及图模式构建###################################
class State(TypedDict):
    """
    状态跟踪
    """
    messages: Annotated[list[AnyMessage], add_messages]


def my_node(state: State):
    last_message = llm.invoke(state["messages"])
    if last_message.tool_calls:
        return Command(
            update={
                # update the message history
                "messages": [last_message],
            },
            goto="tools"
        )
    else:
        return END


def my_other_node(state: State):
    print("__step2__")


workflow = StateGraph(State)
workflow.add_node(my_node)
workflow.add_node(my_other_node)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "my_node")
workflow.add_edge("my_other_node", END)
graph = workflow.compile()

# # 画图
# img = graph.get_graph().draw_mermaid_png()
# image =Image.open(io.BytesIO(img))
# image.save("./command_tool.png")


############################图模式运行######################################
config = {"configurable": {"thread_id": "1"}}
result = graph.invoke({"messages": "帮我查一下张三的信息"}, config)
print(result)


