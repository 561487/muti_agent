from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph import StateGraph, MessagesState
from langgraph.constants import START, END
from operator import add
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt
import os
from langgraph.checkpoint.memory import InMemorySaver
 
#message类型 

llm = ChatOpenAI(
    model="qwen2.5-32b-instruct",
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key=os.getenv("api_key")
)

def human_node(state:MessagesState)->MessagesState:
    
    humman_input= input("用户: ")
    "根据用户的输入 改变状态"
    return {"messages": HumanMessage(content=humman_input)}

def llm_node(state:MessagesState)->MessagesState:
    response=llm.invoke(state["messages"])
    #print (response.content)
    return {"messages": response}
#MessagesState特殊的字典
builder = StateGraph(MessagesState)
builder.add_node("human_node", human_node)
builder.add_node("llm_node", llm_node)  
builder.add_edge(START, "human_node")
builder.add_edge("human_node","llm_node")
builder.add_edge("llm_node", END)

graph = builder.compile()
result=graph.invoke({"messages":SystemMessage(content="我是智能聊天机器人")})
print (result)
# print(graph.invoke({"documents": ["你好"]}))
