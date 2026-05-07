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
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import asyncio
#长期记忆，持久化存储

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

async def main():
    print ("你可以和机器人聊天了！！！")
    #对话数据存在数据库里
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as memory:
        graph = builder.compile(checkpointer=memory)
        user_id= input("请输入user_id: ")
        await graph.ainvoke({},config={"configurable": {"thread_id":user_id}})
        while True:
            user_id= input("请输入user_id: ")
            if user_id=="退出":
                break
            await graph.ainvoke({},config={"configurable": {"thread_id":user_id}})
asyncio.run(main())

