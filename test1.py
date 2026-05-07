from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.constants import START, END
###langgraph初步
#数据流在图上传播
#数据一定要是字典行，TypedDict做一个强制判断
class MyState(TypedDict):
    foo: str


#{"foo":"My"}
def node_1(state: MyState) -> MyState:
    # Write to OverallState
    #{"foo": "My name"}
    print ("node1",state)
    return {"foo": state["foo"] + " name"}

def node_2(state: MyState) -> MyState:
    #{"foo": "My name is"}
    return {"foo": state["foo"] + " is"}

def node_3(state: MyState) -> MyState:
    #{"foo": "My name is Lance"}
    return {"foo": state["foo"] + " Lance"}
#构建一张图
builder = StateGraph(MyState )
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)
#START  END特殊字段
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", "node_3")
builder.add_edge("node_3", END)

graph = builder.compile()
#图开始进行操作，传入信息，字典型并满足
result=graph.invoke({"foo":"My"})
print (result)