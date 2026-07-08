"""
Error classification and graceful degradation for agent nodes.

Distinguishes transient failures (retryable) from permanent errors,
and prevents pipeline-wide crashes by returning partial results when
individual agents fail.
"""

import structlog
from functools import wraps

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


def classify_error(error: Exception) -> str:
    """
    Classify an error as 'retryable', 'degraded', or 'fatal'.

    Args:
        error: The caught exception.

    Returns:
        One of ``'retryable'``, ``'fatal'``.

    Raises:
        KeyboardInterrupt: Always propagated immediately.
        SystemExit: Always propagated immediately.
    """
    # Never swallow intentional process signals
    if isinstance(error, (KeyboardInterrupt, SystemExit)):
        raise

    if isinstance(error, RETRYABLE_EXCEPTIONS):
        return "retryable"

    return "fatal"


def make_agent_node_with_error_handler(agent, agent_name: str):
    """
    Wrap a ReAct agent with error handling for graceful degradation.

    On retryable errors: re-raises so RetryPolicy can retry.
    On fatal errors: returns a degraded Command that allows the
    supervisor to continue with available information.

    Args:
        agent: A compiled ReAct agent (from create_react_agent).
        agent_name: Human-readable name for the agent (for logging/messages).

    Returns:
        A LangGraph node function with error handling.
    """

    def node(state) -> Command:
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
        except Exception as e:
            classification = classify_error(e)
            logger.error(
                "agent_error",
                agent=agent_name,
                error_type=type(e).__name__,
                error=str(e)[:500],
                classification=classification,
            )

            if classification == "retryable":
                raise  # Let RetryPolicy handle it

            # Fatal: return degraded response so the team can continue
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=(
                                f"[{agent_name}] encountered a non-recoverable error "
                                f"({type(e).__name__}). The team will continue with "
                                f"available information."
                            ),
                            name=agent_name,
                        )
                    ]
                },
                goto="supervisor",
            )

    return node
