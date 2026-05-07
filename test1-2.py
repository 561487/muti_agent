from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.constants import START, END
import asyncio
import time
###langgraph初步
#异步处理机制
class MyState(TypedDict):
    foo: str
def node_1(state: MyState) -> MyState:
    # Write to OverallState
    time.sleep(1)
    return {"foo": state["foo"] + " name"}

def node_2(state: MyState) -> MyState:
    print (state)
    return {"foo": state["foo"] + " is"}

def node_3(state: MyState) -> MyState:
 
    return {"foo": state["foo"] + " Lance"}

builder = StateGraph(MyState )
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", "node_3")
builder.add_edge("node_3", END)

graph = builder.compile()
async  def run():
    # r=await graph.ainvoke({"foo":"My"})
    # print (r)
    #两张图
    tasks=[graph.ainvoke({"foo":"My"}),graph.ainvoke({"foo":"My"})]
    #并行处理
    result= await asyncio.gather(*tasks)
    print (result)
asyncio.run(run())

#串行两张图
# result1=graph.invoke({"foo":"My"})
# print (result1)
# result2=graph.invoke({"foo":"My"})
# print (result2)