import io
from typing import TypedDict
from langgraph.constants import START, END
 
from langgraph.types import interrupt, Command
# from IPython.display import Image, display


def node1(state):
    print ("node1")
    return  Command(goto="node3")


def node2(state):
    print ("node2")
    return  Command(goto="node3")

def node3(state):
    print ("node3")
    return  Command(goto="node1")
 

builder = StateGraph(dict)
# builder.add_node("node", node)
builder.add_node("odd_node", odd_node)
builder.add_node("even_node", even_node)
# builder.set_entry_point("odd_node")
# builder.set_conditional_entry_point(condition_edge)
builder.set_conditional_entry_point(condition_edge_bool, {True: "even_node", False: "odd_node"})
# builder.add_conditional_edges("node", condition_edge)
# builder.add_conditional_edges("node", condition_edge_bool, {True: "even_node", False: "odd_node"})
builder.add_edge("odd_node", END)
builder.add_edge("even_node", END)

graph = builder.compile()

img = graph.get_graph().draw_mermaid_png()
image =Image.open(io.BytesIO(img))
image.save("./entry_point.png")

print(graph.invoke({"x": 3, "y": 3}))
