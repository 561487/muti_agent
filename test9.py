from typing import Annotated
from typing_extensions import TypedDict

from langchain_tavily import TavilySearch
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
import os
#时间旅行
class State(TypedDict):
	messages: Annotated[list, add_messages]

llm = ChatOpenAI(
    model="qwen2.5-32b-instruct",
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key=os.getenv("api_key")
)

graph_builder = StateGraph(State)
os.environ["TAVILY_API_KEY"] = "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"
tool = TavilySearch(max_results=2)
tools = [tool]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
	return { "messages": [ llm_with_tools.invoke(state["messages"]) ] }

graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
	"chatbot",
	tools_condition
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)
config = { "configurable": { "thread_id": "1" } }
events = graph.stream(
	{
		"messages": [
			{
				"role": "user",
				"content": (
					"I'm learning LangGraph. "
					"Could you do some research on it for me?"
				)
			}
		]
	},
	config,
	stream_mode="values"
)
for event in events:
	if "messages" in event:
		event["messages"][-1].pretty_print()
print ()
to_replay = None
for state in graph.get_state_history(config):
	print("Num Messages: ", len(state.values["messages"]), "Next: ", state.next)
	print("-" * 80)
	if len(state.values["messages"]) == 2:
		to_replay = state
for event in graph.stream(None, to_replay.config, stream_mode="values"):
	if "messages" in event:
		event["messages"][-1].pretty_print()