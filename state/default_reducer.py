from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from operator import add


class State1(TypedDict):
    foo: int
    bar: list[str]


class State2(TypedDict):
    foo: int
    bar: Annotated[list[str], add]


def node(state):
    return {"bar": ["name"]}


builder = StateGraph(State2)
builder.add_node("node", node)
builder.add_edge(START, "node")
builder.add_edge("node", END)

graph = builder.compile()
print(graph.invoke({"foo": 2, "bar": ["my"]}))
