"""
LLM Provider Factory

Creates and manages LLM provider instances.
"""
from typing import Optional

from core.llm.provider import ILLMProvider
from core.llm.config import get_llm_settings
from core.llm.openai_provider import create_openai_provider, OPENAI_AVAILABLE
from core.llm.mock_provider import create_mock_provider
from shared.exceptions import InternalError


# Global provider instance
_provider: Optional[ILLMProvider] = None


def create_llm_provider(provider_type: Optional[str] = None) -> ILLMProvider:
    """
    Create an LLM provider instance.
    
    Args:
        provider_type: Provider type override (openai, mock)
        
    Returns:
        Configured LLM provider
        
    Raises:
        InternalError: If provider cannot be created
    """
    settings = get_llm_settings()
    provider_type = provider_type or settings.llm_provider
    
    if provider_type == "openai":
        if not OPENAI_AVAILABLE:
            raise InternalError(
                "OpenAI provider not available. Install with: pip install openai"
            )
        if not settings.openai_api_key:
            raise InternalError(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )
        return create_openai_provider(
            api_key=settings.openai_api_key,
            timeout_seconds=settings.openai_timeout_seconds,
        )
    
    elif provider_type == "mock":
        return create_mock_provider()
    
    else:
        raise InternalError(
            f"Unknown LLM provider: {provider_type}. "
            f"Supported providers: openai, mock"
        )


class LLMProviderFactory:
    """Compatibility facade for older module code."""

    @staticmethod
    def get_provider(provider_type: Optional[str] = None) -> ILLMProvider:
        if provider_type:
            return create_llm_provider(provider_type)
        return get_llm_provider()



def get_llm_provider() -> ILLMProvider:
    """
    Get or create global LLM provider instance.
    
    Returns:
        LLM provider singleton
    """
    global _provider
    if _provider is None:
        _provider = create_llm_provider()
    return _provider


def set_llm_provider(provider: ILLMProvider) -> None:
    """
    Set global LLM provider (useful for testing).
    
    Args:
        provider: LLM provider instance
    """
    global _provider
    _provider = provider


def reset_llm_provider() -> None:
    """Reset global LLM provider (useful for testing)."""
    global _provider
    _provider = None
