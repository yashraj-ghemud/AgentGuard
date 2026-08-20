"""
LLM Provider Interface

Abstraction for Large Language Model providers.
Supports structured output generation and keeps business logic independent of provider choice.
"""
from abc import ABC, abstractmethod
from typing import Type, Optional, Any, Dict
from pydantic import BaseModel


class ILLMProvider(ABC):
    """
    Interface for LLM providers.
    
    Implementations can support:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Google (Gemini)
    - Local models (Llama, Mistral)
    
    Business logic should NEVER depend on a specific provider.
    """

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        """
        Generate structured output conforming to a Pydantic schema.
        
        Args:
            prompt: User prompt
            schema: Pydantic model class to validate output
            model: Model identifier (provider-specific)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system instructions
            
        Returns:
            Instance of schema class with validated data
            
        Raises:
            ValidationError: If LLM output doesn't match schema
            TimeoutError: If request times out
            RateLimitError: If rate limit exceeded
            InternalError: For provider-specific errors
        """
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate unstructured text response.
        
        Args:
            prompt: User prompt
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            system_prompt: Optional system instructions
            
        Returns:
            Generated text string
            
        Raises:
            TimeoutError: If request times out
            RateLimitError: If rate limit exceeded
            InternalError: For provider-specific errors
        """
        pass

    @abstractmethod
    async def generate_embeddings(
        self,
        texts: list[str],
        model: str,
    ) -> list[list[float]]:
        """
        Generate embeddings for semantic similarity.
        
        Args:
            texts: List of text strings to embed
            model: Embedding model identifier
            
        Returns:
            List of embedding vectors
            
        Raises:
            InternalError: For provider-specific errors
        """
        pass

    @abstractmethod
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a model.
        
        Args:
            model: Model identifier
            
        Returns:
            Dictionary with model metadata (context_length, pricing, etc.)
        """
        pass

    @abstractmethod
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> float:
        """
        Estimate cost for a request.
        
        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            model: Model identifier
            
        Returns:
            Estimated cost in USD
        """
        pass


class LLMUsageMetrics(BaseModel):
    """Metrics for LLM usage tracking."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    latency_ms: float
    estimated_cost: float


class LLMResponse(BaseModel):
    """Generic LLM response wrapper."""
    content: str
    model: str
    usage: LLMUsageMetrics
    finish_reason: str  # 'stop', 'length', 'content_filter', etc.
