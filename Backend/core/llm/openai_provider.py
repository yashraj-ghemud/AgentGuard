"""
OpenAI LLM Provider Implementation

Implements ILLMProvider for OpenAI models (GPT-4, GPT-3.5, etc.)
"""
import json
import time
from typing import Type, Optional, Any, Dict, List
from pydantic import BaseModel, ValidationError as PydanticValidationError

try:
    from openai import AsyncOpenAI, OpenAIError, RateLimitError as OpenAIRateLimitError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None
    OpenAIError = Exception
    OpenAIRateLimitError = Exception

from core.llm.provider import ILLMProvider, LLMUsageMetrics
from shared.exceptions import (
    ValidationError,
    TimeoutError,
    RateLimitError,
    InternalError,
)


# Model pricing (per 1M tokens) - Updated as of 2024
OPENAI_PRICING = {
    "gpt-4-turbo-preview": {"input": 10.0, "output": 30.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-32k": {"input": 60.0, "output": 120.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "gpt-3.5-turbo-16k": {"input": 3.0, "output": 4.0},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
    "text-embedding-3-large": {"input": 0.13, "output": 0.0},
    "text-embedding-ada-002": {"input": 0.10, "output": 0.0},
}

# Model context lengths
MODEL_CONTEXT_LENGTHS = {
    "gpt-4-turbo-preview": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-3.5-turbo": 16385,
    "gpt-3.5-turbo-16k": 16385,
}


class OpenAIProvider(ILLMProvider):
    """OpenAI implementation of ILLMProvider."""

    def __init__(self, api_key: str, timeout_seconds: int = 60):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            timeout_seconds: Request timeout
            
        Raises:
            ImportError: If openai package not installed
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )
        
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self.timeout_seconds = timeout_seconds

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        """Generate structured output using OpenAI function calling."""
        start_time = time.time()
        
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Convert Pydantic schema to OpenAI function schema
            function_schema = {
                "name": "output",
                "description": f"Structured output conforming to {schema.__name__}",
                "parameters": schema.model_json_schema(),
            }
            
            # Call OpenAI with function calling
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                functions=[function_schema],
                function_call={"name": "output"},
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Extract function call arguments
            message = response.choices[0].message
            if not message.function_call:
                raise InternalError(
                    "OpenAI did not return function call",
                    details={"finish_reason": response.choices[0].finish_reason}
                )
            
            # Parse and validate JSON
            try:
                data = json.loads(message.function_call.arguments)
                result = schema.model_validate(data)
            except json.JSONDecodeError as e:
                raise ValidationError(
                    f"Invalid JSON from OpenAI: {str(e)}",
                    details={"raw_output": message.function_call.arguments}
                )
            except PydanticValidationError as e:
                raise ValidationError(
                    f"Output doesn't match schema: {str(e)}",
                    details={"validation_errors": e.errors()}
                )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Track usage (attached as metadata to result)
            if hasattr(result, '__dict__'):
                result.__dict__['_llm_usage'] = LLMUsageMetrics(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                    model=model,
                    latency_ms=latency_ms,
                    estimated_cost=self.estimate_cost(
                        response.usage.prompt_tokens,
                        response.usage.completion_tokens,
                        model,
                    ),
                )
            
            return result
            
        except OpenAIRateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}")
        except OpenAIError as e:
            if "timeout" in str(e).lower():
                raise TimeoutError("OpenAI request", self.timeout_seconds)
            raise InternalError(f"OpenAI error: {str(e)}")

    async def generate_text(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate unstructured text using OpenAI chat completion."""
        start_time = time.time()
        
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
            if not content:
                raise InternalError(
                    "OpenAI returned empty response",
                    details={"finish_reason": response.choices[0].finish_reason}
                )
            
            return content
            
        except OpenAIRateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}")
        except OpenAIError as e:
            if "timeout" in str(e).lower():
                raise TimeoutError("OpenAI request", self.timeout_seconds)
            raise InternalError(f"OpenAI error: {str(e)}")

    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small",
    ) -> List[List[float]]:
        """Generate embeddings using OpenAI embedding models."""
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=texts,
            )
            
            # Extract embeddings in order
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except OpenAIRateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}")
        except OpenAIError as e:
            raise InternalError(f"OpenAI error: {str(e)}")

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get OpenAI model information."""
        return {
            "model": model,
            "provider": "openai",
            "context_length": MODEL_CONTEXT_LENGTHS.get(model, 4096),
            "pricing": OPENAI_PRICING.get(model, {"input": 0.0, "output": 0.0}),
            "supports_functions": model.startswith("gpt-"),
            "supports_embeddings": model.startswith("text-embedding-"),
        }

    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> float:
        """Estimate cost for OpenAI request."""
        pricing = OPENAI_PRICING.get(model, {"input": 0.0, "output": 0.0})
        
        # Pricing is per 1M tokens
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost


def create_openai_provider(api_key: str, timeout_seconds: int = 60) -> OpenAIProvider:
    """
    Factory function to create OpenAI provider.
    
    Args:
        api_key: OpenAI API key
        timeout_seconds: Request timeout
        
    Returns:
        Configured OpenAI provider
    """
    return OpenAIProvider(api_key=api_key, timeout_seconds=timeout_seconds)
