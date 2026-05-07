import uuid
from typing import Optional
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command

##########################图模式构建###################################
class State(TypedDict):
    """图状态"""

    foo: str
    human_value: Optional[str]  # 通过interrupt更新人类输入值


def node(state: State):
    answer = interrupt(
        # interrupt中的值将通过作为终端信息传递至客户端
        "你是谁"
    )
    print(f"> Received an input from the interrupt: {answer}")
    return {"human_value": answer}


builder = StateGraph(State)
builder.add_node("node", node)
builder.add_edge(START, "node")

# 使用interrupt必须构建checkpointer
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {
    "configurable": {
        "thread_id": uuid.uuid4(),
    }
}

#########################状态图运行#################################
for chunk in graph.stream({"foo": "abc"}, config):
    print(chunk)

print("-----------------------")

command = Command(resume="我是张三")

for chunk in graph.stream(command, config):
    print(chunk)

