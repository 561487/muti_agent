from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from operator import add


def combine(a, b):
    return 2*a + 2*b


class State3(TypedDict):
    foo: int
    bar: Annotated[list[str], combine]


def node(state):
    # Write to OverallState
    return {"bar": ["name"]}


def node1(state):
    return {"bar": ["is"]}


builder = StateGraph(State3)
builder.add_node("node", node)
builder.add_node("node1", node1)
builder.add_edge(START, "node")
builder.add_edge("node", "node1")
builder.add_edge("node1", END)

graph = builder.compile()
print(graph.invoke({"foo": 2, "bar": ["my"]}))
