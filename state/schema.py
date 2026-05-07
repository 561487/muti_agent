import io
from typing import TypedDict
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from PIL import Image
# from IPython.display import Image, display


def add_node(state):
    # Write to OverallState
    return {"x": state["x"] + state["y"], "y": state["y"]}


def mul_node(state):
    # Write to OverallState
    return {"x": state["x"] * state["y"], "y": state["y"]}


builder = StateGraph(dict)
builder.add_node("add_node", add_node)
builder.add_node("mul_node", mul_node)
builder.add_edge(START, "add_node")
builder.add_edge("add_node", "mul_node")
builder.add_edge("mul_node", END)

graph = builder.compile()
print(graph.get_graph())

# img = graph.get_graph().draw_mermaid_png()
# image =Image.open(io.BytesIO(img))
# image.save("./img.png")
# display(Image(graph.get_graph(xray=True).draw_mermaid_png()))
print(graph.invoke({"x": 2, "y": 3}))
