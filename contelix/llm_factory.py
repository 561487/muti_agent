"""
LLM factory — provides thread-safe, cacheable ChatOpenAI instances.

Replaces module-level ``_llm = ChatOpenAI(...)`` instantiation with a
factory pattern that enables testing with mock models, runtime model
switching, and future fallback model support.
"""

import threading
from typing import Optional

from langchain_openai import ChatOpenAI

from contelix.config import (
    MODEL_NAME,
    MODEL_BASE_URL,
    MODEL_API_KEY,
    MODEL_TEMPERATURE,
)

_llm_cache: dict[str, ChatOpenAI] = {}
_cache_lock = threading.Lock()


def get_llm(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
) -> ChatOpenAI:
    """
    Get or create a cached ChatOpenAI instance.

    Instances are cached by (model_name, temperature) key. Thread-safe
    via a lock — safe for concurrent graph execution.

    Args:
        model_name: Override the default model. Uses CONTELIX_MODEL_NAME if None.
        temperature: Override the default temperature. Uses MODEL_TEMPERATURE if None.

    Returns:
        A configured ChatOpenAI instance with built-in retry (max_retries=2).
    """
    cache_key = f"{model_name or MODEL_NAME}_{temperature if temperature is not None else MODEL_TEMPERATURE}"

    with _cache_lock:
        if cache_key not in _llm_cache:
            _llm_cache[cache_key] = ChatOpenAI(
                model=model_name or MODEL_NAME,
                base_url=MODEL_BASE_URL,
                api_key=MODEL_API_KEY,
                temperature=temperature if temperature is not None else MODEL_TEMPERATURE,
                max_retries=2,
                request_timeout=120,
            )
        return _llm_cache[cache_key]
