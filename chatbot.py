import io
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from PIL import Image


@tool
def search_weather(city):
    """查询天气

    arg: 城市
    """
    return f"搜索到{city}的天气了，天气晴朗，温度23摄氏度"

#条件转移，结束或者继续调用工具
def should_continue(state):
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    else:
        return END


tools = [search_weather]
#构建工具节点
tool_node = ToolNode(tools)
#构建大模型
llm = ChatOpenAI(
    model="qwen2.5-32b-instruct",
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key="sk-0baadaecdc344279af4efb46d9ff0ba1"
).bind_tools(tools)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_edge(START, "chatbot")
#chatbot可以选择tool，或者直接结束
graph_builder.add_conditional_edges("chatbot",should_continue)
#调用工具后，返回给chatbot
graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile()

# img = graph.get_graph().draw_mermaid_png()
# with open("chatbot.jpg", "wb") as f:
#     f.write(img)

for event in graph.stream({"messages": [{"role": "user", "content": "上海和北京的天气怎么样"}]}):
#for event in graph.stream({"messages": [{"role": "user", "content": "上海的天气怎么样"},{"role": "user", "content": "北京的天气怎么样"}]}):
    print(event)
    # for value in event.values():
    #     print(value)
    #     print("Assistant:", value["messages"][-1].content)
