import io
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph
from langgraph.types import Send
from operator import add
from langgraph.graph import START, END
from PIL import Image
import uuid
from typing import Optional
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command
 



import asyncio
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
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
import dill
from langgraph.types import interrupt, Command
 

 
 
def node1(state: MessagesState)->MessagesState:
    print ("node1")
    return Command(update={"messages":"1"},goto="node2")
def node2(state: MessagesState)->MessagesState:
    print ("node2")
    return Command(update={"messages":"2"}, goto="node3")
def node3(state: MessagesState)->MessagesState:
    print ("node3")
    return Command(update={"messages":"3"}, goto=END)
def node4(state: MessagesState)->MessagesState:
    print ("node4")
    return Command(update={"messages":"4"}, goto=END)
 
 
builder = StateGraph(MessagesState)
builder.add_node("node1", node1)
builder.add_node("node2", node2)
builder.add_node("node3", node3)
builder.add_node("node4", node4)
builder.add_edge("node1", "node4")
builder.add_edge(START, "node1")
 
graph = builder.compile()
result=graph.invoke({})
print (result)
 
 