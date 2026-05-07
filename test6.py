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


#大模型 使用外部的工具
@tool
def add(a: int, b: int) -> int:
    """Adds a and b."""
    return a + b
@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b."""
    return a * b
 

def llm_node(state:MessagesState)->MessagesState:
    response=llm_with_tools.invoke(state["messages"])
    return {"messages": response}

def execute_tools_node(state: MessagesState) -> MessagesState:
    # 执行所有待处理的工具调用
    results=[]
    messages = state["messages"]
    last_message = messages[-1]
    for tool_call in last_message.tool_calls:
        tool_result =tools_by_name[tool_call["name"]].invoke(tool_call["args"])
        results.append(ToolMessage(content=tool_result,tool_call_id=tool_call["id"]))
    return {"messages":results}
#条件边
def should_continue(state:MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    #判断是否调用工具
    if not last_message.tool_calls:
        return "END"
    # Otherwise if there is, we continue
    else:
        return "execute_tools"


tools = [add, multiply]
tools_by_name = {tool.name: tool for tool in tools}
llm = ChatOpenAI(
    model="qwen2.5-32b-instruct",
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key=os.getenv("api_key")
)
#大模型获取了工具的描述信息，但是还不具备直接执行工具的能力
llm_with_tools = llm.bind_tools(tools)


builder = StateGraph(MessagesState )
builder.add_node("llm_node", llm_node)
builder.add_node("execute_tools_node", execute_tools_node)
builder.add_edge(START, "llm_node")
builder.add_edge("execute_tools_node", "llm_node")
builder.add_conditional_edges("llm_node",should_continue,path_map={"execute_tools": "execute_tools_node","END": END})
 

graph = builder.compile()
result=graph.invoke({"messages":"6*3是多少"})
#print (result)
for s in result["messages"]:
    print (type(s),s.content)




# result=llm_with_tools.invoke("6*3是多少?5+7是多少")
# print (result)
# # img = llm_with_tools.get_graph().draw_mermaid_png()
# image =Image.open(io.BytesIO(img))
# image.save("./graph.png")

 