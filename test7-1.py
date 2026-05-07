import io
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph
from langgraph.types import Send
from operator import add
from langgraph.graph import START, END
from PIL import Image
 
#Send功能
class OverallState(TypedDict):
    subjects: list[str]
    jokes: Annotated[list[str], add]


def continue_to_jokes(state: OverallState):
    results=[]
    for s in state['subjects']:
        if s=="life":
            results.append(Send("generate_english_joke", {"subject": s}))
        else:
            results.append(Send("generate_chinese_joke", {"subject": s}))
    return results
def generate_english_joke(state):
    return {"jokes":[f"joke about {state['subject']}"]}
def generate_chinese_joke(state):
    return {"jokes":[f"关于 {state['subject']}的笑话"]}
graph = StateGraph(OverallState)
graph.add_conditional_edges(START, continue_to_jokes)
#graph.add_node("generate_joke", lambda state: {"jokes": [f"joke about {state['subject']}"]})
graph.add_node("generate_english_joke",generate_english_joke)
graph.add_node("generate_chinese_joke",generate_chinese_joke)
graph.add_edge("generate_english_joke", END)
graph.add_edge("generate_chinese_joke", END)
app = graph.compile()
print(app.invoke({"subjects": ["life", "travel"]}))

# img = app.get_graph().draw_mermaid_png()
# image =Image.open(io.BytesIO(img))
# image.save("./send.png")

