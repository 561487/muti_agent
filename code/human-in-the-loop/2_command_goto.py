import io
from typing import Literal
from typing_extensions import TypedDict
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END
from PIL import Image


##########################图模式构建###################################
class State(TypedDict):
    """The graph state."""
    foo: str


def my_node(state: State) -> Command[Literal["my_other_node"]]:
    return Command(
        # state update
        update={"foo": "bar"},
        # control flow
        goto="my_other_node"
    )


def my_other_node(state: State):
    print("receive request")


workflow = StateGraph(State)
workflow.add_node(my_node)
workflow.add_node(my_other_node)
workflow.add_edge(START, "my_node")
workflow.add_edge("my_node", END)
graph = workflow.compile()

# # 画图
# img = graph.get_graph().draw_mermaid_png()
# image =Image.open(io.BytesIO(img))
# image.save("./2_command_goto.png")


#######################图实例运行##################################
config = {"configurable": {"thread_id": "1"}}
result = graph.invoke({"foo": ""}, config)
print(result)


