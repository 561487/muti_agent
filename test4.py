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


#记忆系统，用户隔离
#短期记忆
llm = ChatOpenAI(
    model="qwen2.5-32b-instruct",
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key=os.getenv("api_key")
)

def human_node(state:MessagesState)->MessagesState:
    
    humman_input= input("用户: ")



    return {"messages": HumanMessage(content=humman_input)}

def llm_node(state:MessagesState)->MessagesState:
   
    response=llm.invoke(state["messages"])
    print (response.content)
    return {"messages": response}
 

builder = StateGraph(MessagesState)
builder.add_node("human_node", human_node)
builder.add_node("llm_node", llm_node)  
builder.add_edge(START, "human_node")
builder.add_edge("human_node","llm_node")
builder.add_edge("llm_node", END)

 
print ("你可以和机器人聊天了！！！")
#对话数据存在内存里
memory=InMemorySaver()  
graph = builder.compile(checkpointer=memory)
user_id= input("请输入user_id: ")
graph.invoke({},config={"configurable": {"thread_id":user_id}})
while True:
    user_id= input("请输入user_id: ")
    if user_id=="退出":
        break
    graph.invoke({},config={"configurable": {"thread_id":user_id}})
# # for s in 
# history=graph.get_state (config={"configurable": {"thread_id":123}})
# for s in history.values["messages"]:
#     print (s.content)


