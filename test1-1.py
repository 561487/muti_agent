from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.constants import START, END
###langgraph初步,只会输出state里面定义的字段
class MyState(TypedDict):
    foo: str
    node2:int
    
def node_1(state: MyState) -> MyState:
    # Write to OverallState
    return {"foo": state["foo"] + " name","node1":1}

def node_2(state: MyState) -> MyState:
    print ("node2 input",state)
    return {"foo": state["foo"] + " is","node2":2}

def node_3(state: MyState) -> MyState:
    print ("node3 input",state)
    return {"foo": state["foo"] + " Lance","node3":3}

builder = StateGraph(MyState )
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", "node_3")
builder.add_edge("node_3", END)

graph = builder.compile()
result=graph.invoke({"foo":"My"})
print (result)