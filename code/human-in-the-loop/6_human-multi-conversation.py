import random
import uuid
from typing import Annotated, Literal
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState, create_react_agent
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from config import *


#########################工具及大模型创建############################
@tool
def get_travel_recommendations():
    """旅行地推荐"""
    return random.choice(["北京", "上海"])
    # return "北京"


@tool
def get_hotel_recommendations(location: Literal["北京", "上海"]):
    """推荐给定旅行地的酒店"""
    return {
        "北京": ["西城区希尔顿酒店", "海淀区喜来登酒店"],
        "上海": ["静安区四季酒店", "虹桥区假日酒店"],
    }[location]


def make_handoff_tool(*, agent_name: str):
    """Create a tool that can return handoff via a Command"""
    tool_name = f"transfer_to_{agent_name}"

    @tool(tool_name)
    def handoff_to_agent(
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        """请求另一个agent的帮助"""
        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": tool_name,
            "tool_call_id": tool_call_id,
        }
        return Command(
            # navigate to another agent node in the PARENT graph
            goto=agent_name,
            graph=Command.PARENT,
            update={"messages": state["messages"] + [tool_message]},
        )

    return handoff_to_agent


# 定义旅游专家工具
travel_advisor_tools = [
    get_travel_recommendations,
    make_handoff_tool(agent_name="hotel_advisor"),
]

# 定义酒店专家工具
hotel_advisor_tools = [
    get_hotel_recommendations,
    make_handoff_tool(agent_name="travel_advisor"),
]

model = ChatOpenAI(
    model=MODEL,
    base_url=BASE_URL,
    api_key=API_KEY
)


###########################智能体创建#################################
# 定义旅游专家智能体
travel_advisor = create_react_agent(
    model,
    travel_advisor_tools,
    prompt=(
        "你是一个一般的旅游专家，可以推荐旅游目的地（例如国家，城市等）。"
        "如果您需要酒店推荐，请向hotel_advisor寻求帮助。"
        "在转移到另一个代理之前，必须包含人类可读的响应。"
    ),
)


def call_travel_advisor(
    state: MessagesState,
) -> Command[Literal["hotel_advisor", "human"]]:
    response = travel_advisor.invoke(state)
    return Command(update=response, goto="human")


# 定义酒店专家智能体
hotel_advisor = create_react_agent(
    model,
    hotel_advisor_tools,
    prompt=(
        "你是酒店专家，可以为指定目的地提供酒店推荐。"
        "如果你需要帮助选择旅游目的地，"
        "请向“travel_advisor”寻求帮助。在转移到另一个代理之前，必须包含人类可读的响应。"
    ),
)


def call_hotel_advisor(
    state: MessagesState,
) -> Command[Literal["travel_advisor", "human"]]:
    response = hotel_advisor.invoke(state)
    return Command(update=response, goto="human")


# 创建用户节点
def human_node(
    state: MessagesState, config
) -> Command[Literal["hotel_advisor", "travel_advisor", "human"]]:
    """
    收集用户输入的节点
    """
    user_input = interrupt(
        value="Ready for user input.",
    )

    return Command(
        update={
            "messages": [
                {
                    "role": "human",
                    "content": user_input,
                }
            ]
        },
        goto="travel_advisor"
    )


###########################图模式构建#####################################
builder = StateGraph(MessagesState)
builder.add_node("travel_advisor", call_travel_advisor)
builder.add_node("hotel_advisor", call_hotel_advisor)
builder.add_node("human", human_node)
builder.add_edge(START, "travel_advisor")

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)


#########################多轮对话开始#####################################
thread_config = {"configurable": {"thread_id": uuid.uuid4()}}
# 请给我推荐一个旅游地
# 这个地方很好，能帮我推荐一个这个地区比较好的酒店嘛
# 我喜欢第一个。你能推荐一些酒店附近的活动吗？
idx = 1
while 1:
    u_input = input("请输入（输入exit退出）：")
    if u_input.lower() == 'exit':
        break
    print(f"--- Conversation Turn {idx} ---")
    print(f"User: {u_input}")

    # 包装对应输入至标准格式
    if idx == 1:
        user_input = {
            "messages": [
                {"role": "user", "content": u_input}
            ]
        }
    else:
        user_input = Command(resume=u_input)

    # 运行图
    for update in graph.stream(
        user_input,
        config=thread_config,
        stream_mode="updates",
    ):
        print(update)
        for node_id, value in update.items():
            if isinstance(value, dict) and value.get("messages", []):
                last_message = value["messages"][-1]
                if isinstance(last_message, dict) or last_message.type != "ai":
                    continue
                print(f"{node_id}: {last_message.content}")
    idx += 1
