"""
Mock LLM Provider for Testing

Provides deterministic responses for testing without API calls.
"""
from typing import Type, Optional, Any, Dict, List
from pydantic import BaseModel

from core.llm.provider import ILLMProvider, LLMUsageMetrics


class MockLLMProvider(ILLMProvider):
    """
    Mock LLM provider for testing.
    
    Returns predefined responses without making actual API calls.
    Useful for:
    - Unit tests
    - Integration tests
    - Development without API keys
    """

    def __init__(self):
        """Initialize mock provider with empty response cache."""
        self.responses: Dict[str, Any] = {}
        self.call_count = 0
        self.last_prompt: Optional[str] = None
        self.last_model: Optional[str] = None

    def set_response(self, key: str, response: Any) -> None:
        """
        Set a predefined response for a prompt.
        
        Args:
            key: Prompt or identifier
            response: Response to return
        """
        self.responses[key] = response

    def set_default_structured_response(self, schema: Type[BaseModel], data: dict) -> None:
        """
        Set default response for any structured request with this schema.
        
        Args:
            schema: Pydantic schema class
            data: Data matching schema
        """
        self.responses[f"_default_{schema.__name__}"] = schema.model_validate(data)

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        """Return mocked structured response."""
        self.call_count += 1
        self.last_prompt = prompt
        self.last_model = model
        
        # Try exact prompt match first
        if prompt in self.responses:
            response = self.responses[prompt]
            if isinstance(response, schema):
                return response
            return schema.model_validate(response)
        
        # Try schema default
        default_key = f"_default_{schema.__name__}"
        if default_key in self.responses:
            response = self.responses[default_key]
            if isinstance(response, schema):
                return response
            return schema.model_validate(response)
        
        # Create minimal valid instance
        # This will fail if schema has required fields without defaults
        try:
            return schema.model_validate({})
        except Exception:
            raise ValueError(
                f"No mock response configured for prompt='{prompt[:50]}...' "
                f"and schema={schema.__name__}. Use set_response() or "
                f"set_default_structured_response()."
            )

    async def generate_text(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Return mocked text response."""
        self.call_count += 1
        self.last_prompt = prompt
        self.last_model = model
        
        # Try exact prompt match
        if prompt in self.responses:
            return str(self.responses[prompt])
        
        # Try default text response
        if "_default_text" in self.responses:
            return str(self.responses["_default_text"])
        
        # Return echo of prompt as fallback
        return f"Mock response for: {prompt[:100]}"

    async def generate_embeddings(
        self,
        texts: List[str],
        model: str,
    ) -> List[List[float]]:
        """Return mocked embeddings."""
        self.call_count += 1
        self.last_model = model
        
        # Return mock embeddings (normalized random-looking vectors)
        # In real use, these would be consistent for same input
        if "_embeddings" in self.responses:
            return self.responses["_embeddings"]
        
        # Generate simple mock embeddings (dimension=1536 like OpenAI)
        import hashlib
        embeddings = []
        for text in texts:
            # Use hash for deterministic "random" values
            hash_bytes = hashlib.md5(text.encode()).digest()
            # Create 1536-dim vector from hash
            embedding = []
            for i in range(1536):
                byte_idx = i % len(hash_bytes)
                embedding.append((hash_bytes[byte_idx] / 255.0) - 0.5)
            embeddings.append(embedding)
        
        return embeddings

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Return mock model info."""
        return {
            "model": model,
            "provider": "mock",
            "context_length": 128000,
            "pricing": {"input": 0.0, "output": 0.0},
            "supports_functions": True,
            "supports_embeddings": True,
        }

    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> float:
        """Mock cost estimation (always returns 0)."""
        return 0.0

    def reset(self) -> None:
        """Reset mock state."""
        self.call_count = 0
        self.last_prompt = None
        self.last_model = None
        # Don't clear responses - allow reuse across tests


def create_mock_provider() -> MockLLMProvider:
    """
    Factory function to create mock provider.
    
    Returns:
        Configured mock provider
    """
    return MockLLMProvider()
