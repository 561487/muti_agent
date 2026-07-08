"""
Shared agent node factory — used by all three team supervisors.

Wraps a ReAct agent as a LangGraph node with built-in error handling:
retryable errors are re-raised for RetryPolicy to handle; fatal errors
return a degraded response so the team can continue.
"""

from typing import Literal

import structlog
from langchain_core.messages import HumanMessage
from langgraph.types import Command

logger = structlog.get_logger(__name__)

# Exception types that warrant a retry (transient failures)
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
    IOError,
)


def make_agent_node(agent, agent_name: str):
    """
    Create a LangGraph node wrapping a ReAct agent with error handling.

    On retryable errors (ConnectionError, TimeoutError, OSError):
    re-raises so RetryPolicy can retry. On fatal errors: returns a
    degraded Command so the supervisor can continue.

    Args:
        agent: A compiled ReAct agent (from ``create_react_agent``).
        agent_name: Human-readable name for logging and message metadata.

    Returns:
        A callable suitable for ``StateGraph.add_node()``.
    """

    def node(state) -> Command[Literal["supervisor"]]:
        try:
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
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            is_retryable = isinstance(exc, RETRYABLE_EXCEPTIONS)
            logger.error(
                "agent_error",
                agent=agent_name,
                error_type=type(exc).__name__,
                error=str(exc)[:500],
                retryable=is_retryable,
            )

            if is_retryable:
                raise  # Let RetryPolicy retry

            # Fatal: return degraded response
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=(
                                f"[{agent_name}] encountered an error "
                                f"({type(exc).__name__}). "
                                "The team will continue with available information."
                            ),
                            name=agent_name,
                        )
                    ]
                },
                goto="supervisor",
            )

    return node
