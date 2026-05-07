from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph import StateGraph, MessagesState
from langgraph.constants import START, END
from operator import add


class State1(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class State2(MessagesState):
    pass


def node(state):
    return {"messages": AIMessage(content="你好呀")}


builder = StateGraph(State2)
builder.add_node("node", node)
builder.add_edge(START, "node")
builder.add_edge("node", END)

graph = builder.compile()
print(graph.invoke({"messages": "你好"}))
# print(graph.invoke({"documents": ["你好"]}))
