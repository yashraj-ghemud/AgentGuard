"""
Tests for LLM Provider abstraction.
"""
import pytest
from pydantic import BaseModel

from core.llm import (
    MockLLMProvider,
    create_mock_provider,
    set_llm_provider,
    get_llm_provider,
    reset_llm_provider,
)


class SampleSchema(BaseModel):
    """Sample schema for testing."""
    name: str
    description: str
    count: int = 0


class TestMockProvider:
    """Test MockLLMProvider."""

    def test_mock_provider_creation(self):
        """Test creating mock provider."""
        provider = create_mock_provider()
        assert provider is not None
        assert isinstance(provider, MockLLMProvider)

    @pytest.mark.asyncio
    async def test_generate_structured_with_preset_response(self):
        """Test structured generation with preset response."""
        provider = create_mock_provider()
        
        # Set response
        provider.set_default_structured_response(
            SampleSchema,
            {"name": "test", "description": "test desc", "count": 5}
        )
        
        # Generate
        result = await provider.generate_structured(
            prompt="Generate something",
            schema=SampleSchema,
            model="mock-model",
        )
        
        assert isinstance(result, SampleSchema)
        assert result.name == "test"
        assert result.description == "test desc"
        assert result.count == 5

    @pytest.mark.asyncio
    async def test_generate_text_with_preset_response(self):
        """Test text generation with preset response."""
        provider = create_mock_provider()
        
        # Set response
        provider.set_response("_default_text", "Mock response text")
        
        # Generate
        result = await provider.generate_text(
            prompt="Generate text",
            model="mock-model",
        )
        
        assert result == "Mock response text"

    @pytest.mark.asyncio
    async def test_generate_text_fallback(self):
        """Test text generation fallback when no preset."""
        provider = create_mock_provider()
        
        # Generate without preset
        result = await provider.generate_text(
            prompt="Test prompt",
            model="mock-model",
        )
        
        assert "Test prompt" in result
        assert result.startswith("Mock response for:")

    @pytest.mark.asyncio
    async def test_generate_embeddings(self):
        """Test embedding generation."""
        provider = create_mock_provider()
        
        # Generate embeddings
        texts = ["hello", "world"]
        embeddings = await provider.generate_embeddings(
            texts=texts,
            model="mock-embedding-model",
        )
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536  # OpenAI dimension
        assert len(embeddings[1]) == 1536
        
        # Embeddings should be deterministic
        embeddings2 = await provider.generate_embeddings(
            texts=texts,
            model="mock-embedding-model",
        )
        assert embeddings[0] == embeddings2[0]
        assert embeddings[1] == embeddings2[1]

    def test_get_model_info(self):
        """Test getting model info."""
        provider = create_mock_provider()
        
        info = provider.get_model_info("mock-model")
        
        assert info["provider"] == "mock"
        assert info["model"] == "mock-model"
        assert info["supports_functions"] is True

    def test_estimate_cost(self):
        """Test cost estimation."""
        provider = create_mock_provider()
        
        cost = provider.estimate_cost(
            prompt_tokens=100,
            completion_tokens=50,
            model="mock-model",
        )
        
        assert cost == 0.0  # Mock provider is free

    def test_call_tracking(self):
        """Test that provider tracks calls."""
        provider = create_mock_provider()
        
        assert provider.call_count == 0
        assert provider.last_prompt is None
        
        # Make call
        provider.set_response("_default_text", "response")
        import asyncio
        asyncio.run(provider.generate_text("test", "model"))
        
        assert provider.call_count == 1
        assert provider.last_prompt == "test"
        assert provider.last_model == "model"

    def test_reset(self):
        """Test resetting provider state."""
        provider = create_mock_provider()
        
        # Make calls
        provider.set_response("key", "value")
        import asyncio
        asyncio.run(provider.generate_text("test", "model"))
        
        assert provider.call_count == 1
        
        # Reset
        provider.reset()
        
        assert provider.call_count == 0
        assert provider.last_prompt is None
        # Responses should still be there
        assert "key" in provider.responses


class TestProviderFactory:
    """Test provider factory functions."""

    def test_set_and_get_provider(self):
        """Test setting and getting global provider."""
        reset_llm_provider()
        
        # Create and set provider
        mock_provider = create_mock_provider()
        set_llm_provider(mock_provider)
        
        # Get provider
        provider = get_llm_provider()
        
        assert provider is mock_provider
        
        # Cleanup
        reset_llm_provider()

    def test_get_provider_creates_default(self):
        """Test that get_llm_provider creates provider if none exists."""
        reset_llm_provider()
        
        # Should create mock provider by default in tests
        # (assuming LLM_PROVIDER env var not set or set to mock)
        provider = get_llm_provider()
        
        assert provider is not None
        
        # Cleanup
        reset_llm_provider()
