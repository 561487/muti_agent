from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.graph import START, END

builder = StateGraph(dict)


def my_node(state: dict, config: RunnableConfig):
    print("In node: ", config["configurable"]["user_id"])
    return {"results": f"Hello, {state['input']}!"}


# The second argument is optional
def my_other_node(state: dict):
    return state


builder.add_node("my_node", my_node)
builder.add_node("other_node", my_other_node)
builder.add_edge(START, "my_node")
builder.add_edge("my_node", "other_node")
builder.add_edge("other_node", END)

graph = builder.compile()
print(graph.invoke(input={"input": "langgraph"}, config={"configurable": {"user_id": "123333"}}))

# print(graph.invoke(input={"input": "langgraph"}, stream_mode="values", {"configurable": {"user_id": "123333"}}))
