from typing import Annotated
from typing_extensions import TypedDict

from langchain_tavily import TavilySearch
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import os
@tool
def check_the_weather(city:str) -> str:
    """获取当前天气

    Args:
        city (str): 城市名称

    Returns:
        天气信息
    """
    return f"{city}的气温30度"
#工具使用
class State(TypedDict):
	messages: Annotated[list, add_messages]

llm = ChatOpenAI(
    model="qwen2.5-32b-instruct",
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key=os.getenv("api_key")
)
llm_with_tools = llm.bind_tools([check_the_weather])
 

graph_builder = StateGraph(State)
def chatbot(state: State):
	return { "messages": [ llm_with_tools.invoke(state["messages"]) ] }

graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=[check_the_weather])
graph_builder.add_node("tools", tool_node)

def condition(state:State):
 
	if "tool_calls" in state["messages"][-1].additional_kwargs:
		return "tools"
	return "END"
graph_builder.add_conditional_edges(
	"chatbot",
	condition
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

memory = MemorySaver()
graph = graph_builder.compile()
 
result = graph.invoke({"messages":"北京天气怎么样"})
print (result)