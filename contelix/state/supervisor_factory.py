"""
Supervisor node factory — creates LLM-based router agents that manage
teams of specialized sub-agents.

This is the core orchestration pattern used at every level of Contelix:
Top-level boss, Research supervisor, Analysis supervisor, Report supervisor.
"""

from typing import Callable, List, Literal, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.graph import END
from langgraph.types import Command
from typing_extensions import TypedDict


def make_supervisor_node(
    llm: BaseChatModel,
    members: List[str],
    system_prompt: Optional[str] = None,
) -> Callable:
    """
    Create a supervisor node that routes tasks to the appropriate sub-agent.

    The supervisor is an LLM-based router: it examines the conversation
    history and decides which team member should act next. When the task
    is complete, it routes to FINISH (which maps to END in the graph).

    Args:
        llm: The LLM instance to use for routing decisions.
        members: List of team member names the supervisor can route to.
        system_prompt: Optional custom system prompt. If not provided,
                       a default prompt is generated from the member list.

    Returns:
        A callable supervisor_node function suitable for use as a
        LangGraph node with StateGraph.add_node().
    """
    member_list = ", ".join(members)
    finish_literal = "FINISH"

    if system_prompt is None:
        system_prompt = (
            f"你是一个 Supervisor，管理以下专家团队: {member_list}。\n\n"
            "你的职责是根据用户请求和当前进展，将任务路由给最合适的专家。\n\n"
            "规则:\n"
            f"1. 每个专家每次只执行一个任务，完成后汇报结果。\n"
            f"2. 将任务路由给专业最匹配的专家。\n"
            f"3. 所有任务完成后，回复 '{finish_literal}'。\n"
            f"4. 除非有新的需求，不要重复委派已经完成任务的专家。\n\n"
            "请返回 JSON 格式: {{\"next\": \"specialist_name\"}}"
        )

    class Router(TypedDict):
        """Route to the next specialist, or FINISH if done."""
        next: str

    def supervisor_node(state: dict) -> Command:
        """The supervisor node — decides which agent acts next."""
        messages = [
            SystemMessage(content=system_prompt),
        ] + list(state.get("messages", []))

        response = llm.with_structured_output(Router).invoke(messages)
        goto = response.get("next", "FINISH")

        if goto == "FINISH":
            goto = END

        return Command(goto=goto)

    return supervisor_node
