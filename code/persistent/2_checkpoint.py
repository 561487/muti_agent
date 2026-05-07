import io
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated
from typing_extensions import TypedDict
from operator import add
from PIL import Image

##########################图模式构建###################################
class State(TypedDict):
    foo: str
    bar: Annotated[list[str], add]


def node_a(state: State):
    return {"foo": "a", "bar": ["a"]}


def node_b(state: State):
    return {"foo": "b", "bar": ["b"]}


workflow = StateGraph(State)
workflow.add_node(node_a)
workflow.add_node(node_b)
workflow.add_edge(START, "node_a")
workflow.add_edge("node_a", "node_b")
workflow.add_edge("node_b", END)

# 定义checkpointer进行图存储
checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)



#############################状态图运行##############################
config = {"configurable": {"thread_id": "1"}}
result = graph.invoke({"foo": ""}, config)
print(result)

# # 画图
# img = graph.get_graph().draw_mermaid_png()
# image =Image.open(io.BytesIO(img))
# image.save("./graph.png")

# 获取历史checkpoint
state_history = list(graph.get_state_history(config))
print(state_history)

# 获取当前checkpoint
current_state = graph.get_state(config)
print("--------------")

# # replay
# config = {"configurable": {"thread_id": "1", "checkpoint_id": state_history[1].config["configurable"]["checkpoint_id"]}}
# result = graph.invoke(None, config=config)
# print(result)

# # update state
# graph.update_state(config, {"foo": "c", "bar": ["c"]})
# print(graph.get_state(config))

# update state指定checkpoint
graph.update_state(state_history[1].config, {"foo": "c", "bar": ["b"]})
print(graph.get_state(config))
result = graph.invoke({"foo": "d", "bar": ["d"]}, config=config)
state_history = list(graph.get_state_history(config))
print(result)
