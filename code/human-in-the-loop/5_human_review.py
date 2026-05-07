from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from config import *


##########################工具及模型构建###################################
@tool
def weather_search(city: str):
    """查询天气

    city: 城市
    """
    print("----")
    print(f"Searching for: {city}")
    print("----")
    return "Sunny!"


model = ChatOpenAI(
    model=MODEL,
    base_url=BASE_URL,
    api_key=API_KEY,
    temperature=0
).bind_tools(
    [weather_search]
)


##########################节点及图模式构建###################################
class State(MessagesState):
    """
    消息状态
    """


def call_llm(state):
    return {"messages": [model.invoke(state["messages"])]}


def human_review_node(state) -> Command[Literal["call_llm", "run_tool"]]:
    """
    人类审核节点
    """
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[-1]

    # this is the value we'll be providing via Command(resume=<human_review>)
    human_review = interrupt(
        {
            "question": "Is this correct?",
            # Surface tool calls for review
            "tool_call": tool_call,
        }
    )

    review_action = human_review["action"]
    review_data = human_review.get("data")

    # 如果同意则直接调用工具
    if review_action == "continue":
        return Command(goto="run_tool")

    # 如果是修改状态则修改调用工具信息后调用工具
    elif review_action == "update":
        updated_message = {
            "role": "ai",
            "content": last_message.content,
            "tool_calls": [
                {
                    "id": tool_call["id"],
                    "name": tool_call["name"],
                    # This the update provided by the human
                    "args": review_data,
                }
            ],
            # This is important - this needs to be the same as the message you replacing!
            # Otherwise, it will show up as a separate message
            "id": last_message.id,
        }
        return Command(goto="run_tool", update={"messages": [updated_message]})

    # 直接提供工具反馈信息
    elif review_action == "feedback":
        # NOTE: we're adding feedback message as a ToolMessage
        # to preserve the correct order in the message history
        # (AI messages with tool calls need to be followed by tool call messages)
        tool_message = {
            "role": "tool",
            # This is our natural language feedback
            "content": review_data,
            "name": tool_call["name"],
            "tool_call_id": tool_call["id"],
        }
        return Command(goto="call_llm", update={"messages": [tool_message]})


def run_tool(state):
    new_messages = []
    tools = {"weather_search": weather_search}
    tool_calls = state["messages"][-1].tool_calls
    for tool_call in tool_calls:
        tool = tools[tool_call["name"]]
        result = tool.invoke(tool_call["args"])
        new_messages.append(
            {
                "role": "tool",
                "name": tool_call["name"],
                "content": result,
                "tool_call_id": tool_call["id"],
            }
        )
    return {"messages": new_messages}


def route_after_llm(state) -> Literal[END, "human_review_node"]:
    if len(state["messages"][-1].tool_calls) == 0:
        return END
    else:
        return "human_review_node"


builder = StateGraph(State)
builder.add_node(call_llm)
builder.add_node(run_tool)
builder.add_node(human_review_node)
builder.add_edge(START, "call_llm")
builder.add_conditional_edges("call_llm", route_after_llm)
builder.add_edge("run_tool", "call_llm")

# 设置checkpointer
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# # no review
# initial_input = {"messages": [{"role": "user", "content": "你好"}]}
# thread = {"configurable": {"thread_id": "1"}}
#
# # Run the graph until the first interruption
# for event in graph.stream(initial_input, thread, stream_mode="updates"):
#     print(event)
#     # print(event["messages"][-1].pretty_print())
#     print("\n")


# # approving tool
# initial_input = {"messages": [{"role": "user", "content": "帮我查一下北京的天气怎么羊"}]}
# thread = {"configurable": {"thread_id": "2"}}
#
# for event in graph.stream(initial_input, thread, stream_mode="updates"):
#     print(event)
#     print("\n")
#
# print("Pending Executions!")
# print(graph.get_state(thread).next)
#
# for event in graph.stream(
#     # provide value
#     Command(resume={"action": "continue"}),
#     thread,
#     stream_mode="updates",
# ):
#     print(event)
#     print("\n")


# # edit tool
# initial_input = {"messages": [{"role": "user", "content": "帮我查一下吉林的天气怎么样"}]}
# thread = {"configurable": {"thread_id": "2"}}
#
# for event in graph.stream(initial_input, thread, stream_mode="updates"):
#     print(event)
#     print("\n")
#
# # Let's now continue executing from here
# for event in graph.stream(
#     Command(resume={"action": "update", "data": {"city": "吉林省"}}),
#     thread,
#     stream_mode="updates",
# ):
#     print(event)
#     print("\n")


# feedback
initial_input = {"messages": [{"role": "user", "content": "帮我查一下明天中国北京的天气怎么样"}]}
thread = {"configurable": {"thread_id": "4"}}

for event in graph.stream(initial_input, thread, stream_mode="updates"):
    print(event)
    print("\n")

print("Pending Executions!")
print(graph.get_state(thread).next)

for event in graph.stream(
    Command(
        resume={
            "action": "feedback",
            "data": "用户需求改变，使用<城市、国家>的格式表示查询信息",
        }
    ),
    thread,
    stream_mode="updates",
):
    print(event)
    print("\n")

print("Pending Executions!")
print(graph.get_state(thread).next)

for event in graph.stream(
    Command(resume={"action": "continue"}), thread, stream_mode="updates"
):
    print(event)
    print("\n")