from typing import Literal, Optional
from typing_extensions import TypedDict
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.constants import START


##########################节点及图模式构建###################################
class State(TypedDict):
    """The graph state."""

    foo: str
    llm_output: Optional[str]


def human_approval(state: State) -> Command[Literal["approve_node", "reject_node"]]:
    """
    用户
    """
    is_approved = interrupt(
        {
            "question": "输出是否正确?",
            "llm_output": state["llm_output"]
        }
    )

    if is_approved:
        return Command(goto="approve_node")
    else:
        return Command(goto="reject_node")


def approve_node(state: State):
    print("Approved")


def reject_node(state: State):
    print("Reject")


graph_builder = StateGraph(State)
graph_builder.add_node("human_approval", human_approval)
graph_builder.add_node("approve_node", approve_node)
graph_builder.add_node("reject_node", reject_node)
graph_builder.add_edge(START, "human_approval")

# 使用interrupt必须构建checkpointer
checkpointer = MemorySaver()
graph = graph_builder.compile(checkpointer=checkpointer)


#########################状态图运行#################################
thread_config = {"configurable": {"thread_id": "1"}}
print(graph.invoke({"foo": "bar", "llm_output": "你好"}, config=thread_config))

# 查看用户输入后的下一步骤
print(graph.get_state(thread_config).next)

# 根据用户输入继续进行图运行
print(graph.invoke(Command(resume=False, update={"llm_output": "True"}), config=thread_config))

