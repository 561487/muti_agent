from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from typing import Annotated,Optional,Literal
from langgraph.graph.message import add_messages
 
###数据的reducer
#字段，提供reducer的方法
def concat_str(
    left: str,#节点输入
    right: str,#节点return
) -> str:
    #真正的输出
    return left+right

class MyState(TypedDict):
    #str表示foo的类型
    #concat_str 对字段的说明，对该字段加了一个附属信息
    foo: Annotated[str,concat_str]
 

def node_1(state: MyState) -> MyState:
    # Write to OverallState
    return {"foo": "你"}

def node_2(state: MyState) -> MyState:
    # Write to OverallState
    return {"foo": "好"}

def node_3(state: MyState) -> MyState:
    # Write to OverallState
    return {"foo": "啊"}

builder = StateGraph(MyState,input=MyState,output=MyState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", "node_3")
builder.add_edge("node_3", END)

graph = builder.compile()
result=graph.invoke({"foo":""})
print (result)