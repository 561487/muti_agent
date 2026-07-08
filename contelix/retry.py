"""
Retry policy configurations for LangGraph agent nodes.
"""

from langgraph.types import RetryPolicy

# Applied to all agent nodes (LLM calls, tool invocations)
AGENT_RETRY_POLICY = RetryPolicy(
    max_attempts=3,
    initial_interval=1.0,
    backoff_factor=2.0,
    max_interval=30.0,
    retry_on=Exception,
)
