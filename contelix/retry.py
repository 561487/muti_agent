"""
Retry policy configuration for LangGraph agent nodes.

Provides pre-configured RetryPolicy instances for different
failure scenarios in the Contelix multi-agent pipeline.
"""

from langgraph.types import RetryPolicy

# Standard retry policy for agent nodes (LLM calls, tool invocations)
AGENT_RETRY_POLICY = RetryPolicy(
    max_attempts=3,
    initial_interval=1.0,
    backoff_factor=2.0,
    max_interval=30.0,
    retry_on=Exception,
)

# Aggressive retry for network-dependent nodes (search, scraping)
NETWORK_RETRY_POLICY = RetryPolicy(
    max_attempts=5,
    initial_interval=0.5,
    backoff_factor=2.0,
    max_interval=15.0,
    retry_on=(ConnectionError, TimeoutError, OSError),
)
