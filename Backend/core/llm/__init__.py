"""
LLM Module

Provides abstraction for Large Language Model providers.
"""
from core.llm.provider import ILLMProvider, LLMUsageMetrics, LLMResponse
from core.llm.factory import (
    create_llm_provider,
    get_llm_provider,
    set_llm_provider,
    reset_llm_provider,
)
from core.llm.config import LLMSettings, get_llm_settings, reset_llm_settings
from core.llm.openai_provider import OpenAIProvider, OPENAI_AVAILABLE
from core.llm.mock_provider import MockLLMProvider, create_mock_provider

__all__ = [
    # Interface
    "ILLMProvider",
    "LLMUsageMetrics",
    "LLMResponse",
    # Factory
    "create_llm_provider",
    "get_llm_provider",
    "set_llm_provider",
    "reset_llm_provider",
    # Configuration
    "LLMSettings",
    "get_llm_settings",
    "reset_llm_settings",
    # Providers
    "OpenAIProvider",
    "OPENAI_AVAILABLE",
    "MockLLMProvider",
    "create_mock_provider",
]
