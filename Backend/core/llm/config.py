"""
LLM Configuration

Configures LLM providers and model policies for different operations.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """LLM-specific configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Provider configuration
    llm_provider: str = Field(
        default="openai",
        description="LLM provider: openai, mock"
    )
    
    # OpenAI configuration
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    openai_organization: Optional[str] = Field(
        default=None,
        description="OpenAI organization ID"
    )
    openai_timeout_seconds: int = Field(
        default=60,
        description="OpenAI request timeout"
    )
    
    # Model policies for different operations
    agent_analysis_model: str = Field(
        default="gpt-4-turbo-preview",
        description="Model for agent capability analysis"
    )
    agent_analysis_temperature: float = Field(
        default=0.3,
        description="Temperature for agent analysis (lower = more focused)"
    )
    
    risk_analysis_model: str = Field(
        default="gpt-4-turbo-preview",
        description="Model for risk analysis"
    )
    risk_analysis_temperature: float = Field(
        default=0.2,
        description="Temperature for risk analysis (lower = more conservative)"
    )
    
    strategy_planning_model: str = Field(
        default="gpt-4-turbo-preview",
        description="Model for test strategy planning"
    )
    strategy_planning_temperature: float = Field(
        default=0.4,
        description="Temperature for strategy planning"
    )
    
    scenario_generation_model: str = Field(
        default="gpt-4-turbo-preview",
        description="Model for scenario generation"
    )
    scenario_generation_temperature: float = Field(
        default=0.7,
        description="Temperature for scenario generation (higher = more creative)"
    )
    
    scenario_review_model: str = Field(
        default="gpt-3.5-turbo",
        description="Model for scenario review/validation"
    )
    scenario_review_temperature: float = Field(
        default=0.2,
        description="Temperature for scenario review"
    )
    
    mutation_model: str = Field(
        default="gpt-3.5-turbo",
        description="Model for adversarial mutations"
    )
    mutation_temperature: float = Field(
        default=0.8,
        description="Temperature for mutations (higher = more varied)"
    )
    
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Model for embeddings (deduplication)"
    )
    
    # Generation limits
    max_scenarios_per_request: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum scenarios per generation request"
    )
    max_generation_timeout_seconds: int = Field(
        default=3600,
        description="Maximum time for entire generation run"
    )
    max_llm_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retries for failed LLM calls"
    )
    max_tokens_per_request: int = Field(
        default=4000,
        description="Maximum tokens per LLM request"
    )
    
    # Quality thresholds
    min_scenario_quality_score: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum quality score for scenarios"
    )
    min_relevance_score: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score for scenarios"
    )
    similarity_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Cosine similarity threshold for duplicate detection"
    )
    
    # Cost controls
    enable_cost_tracking: bool = Field(
        default=True,
        description="Track estimated LLM costs"
    )
    max_cost_per_run: Optional[float] = Field(
        default=None,
        description="Maximum cost per generation run (USD)"
    )
    warn_cost_threshold: float = Field(
        default=10.0,
        description="Cost threshold to trigger warnings (USD)"
    )


# Global settings instance
_llm_settings: Optional[LLMSettings] = None


def get_llm_settings() -> LLMSettings:
    """
    Get LLM settings singleton.
    
    Returns:
        LLMSettings instance
    """
    global _llm_settings
    if _llm_settings is None:
        _llm_settings = LLMSettings()
    return _llm_settings


def reset_llm_settings() -> None:
    """Reset LLM settings singleton (useful for testing)."""
    global _llm_settings
    _llm_settings = None
