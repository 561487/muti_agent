# Set up the tool
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import MessagesState, START
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
import os
from langchain_core.tools import tool
import io
from typing import TypedDict
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from PIL import Image
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, AnyMessage
from langgraph.prebuilt import create_react_agent

#更简单的使用工具
@tool
def add(a: int, b: int) -> int:
    """Adds a and b."""
    return a + b
@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b."""
    return a * b
tools = [add, multiply]

llm = ChatOpenAI(
    model="qwen2.5-32b-instruct",
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key=os.getenv("api_key")
)
graph = create_react_agent(
    llm,
    tools=tools,
 
)
result=graph.invoke({"messages":"6*3是多少"})
#print (result)
for s in result["messages"]:
    print (type(s),s.content)
 