import io
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph
from langgraph.types import Send
from operator import add
from langgraph.graph import START, END
from PIL import Image


class OverallState(TypedDict):
    subjects: list[str]
    jokes: Annotated[list[str], add]


def continue_to_jokes(state: OverallState):
    return [Send("generate_joke", {"subject": s}) for s in state['subjects']]


graph = StateGraph(OverallState)
graph.add_node("generate_joke", lambda state: {"jokes": [f"joke about {state['subject']}"]})
graph.add_conditional_edges(START, continue_to_jokes)
graph.add_edge("generate_joke", END)

app = graph.compile()
print(app.invoke({"subjects": ["life", "travel"]}))

# img = app.get_graph().draw_mermaid_png()
# image =Image.open(io.BytesIO(img))
# image.save("./send.png")

