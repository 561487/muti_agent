"""
Shared agent node factory — used by all three team supervisors.

Extracts the common pattern of wrapping a ReAct agent as a LangGraph
node that reports back to the team supervisor.
"""

from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command


def make_agent_node(agent, agent_name: str):
    """
    Create a LangGraph node wrapping a ReAct agent.

    The node invokes the agent with the current state, extracts the last
    AI message, wraps it in a HumanMessage (for the supervisor to read),
    and routes back to ``"supervisor"``.

    Args:
        agent: A compiled ReAct agent (from ``create_react_agent``).
        agent_name: Human-readable name for the agent (used in message metadata).

    Returns:
        A callable suitable for ``StateGraph.add_node()``.
    """

    def node(state) -> Command[Literal["supervisor"]]:
        result = agent.invoke(state)
        last_msg = result["messages"][-1]
        return Command(
            update={
                "messages": [
                    HumanMessage(content=last_msg.content, name=agent_name)
                ]
            },
            goto="supervisor",
        )

    return node
