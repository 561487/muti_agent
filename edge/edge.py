import io
from typing import TypedDict
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from PIL import Image
# from IPython.display import Image, display


def node(state):
    return state


def odd_node(state):
    state["x"] = state["x"] - 1
    return state


def even_node(state):
    state["x"] = state["x"] // 2
    return state


def condition_edge(state):
    if state["x"] // 2 == 0:
        return "even_node"
    else:
        return "odd_node"


def condition_edge_bool(state):
    if state["x"] // 2 == 0:
        return True
    else:
        return False


builder = StateGraph(dict)
builder.add_node("node", node)
builder.add_node("odd_node", odd_node)
builder.add_node("even_node", even_node)
builder.add_edge(START, "node")
# builder.add_conditional_edges("node", condition_edge)
builder.add_conditional_edges("node", condition_edge_bool, {True: "even_node", False: "odd_node"})
builder.add_edge("odd_node", END)
builder.add_edge("even_node", END)

graph = builder.compile()

img = graph.get_graph().draw_mermaid_png()
image =Image.open(io.BytesIO(img))
image.save("./img1.png")

print(graph.invoke({"x": 2, "y": 3}))
