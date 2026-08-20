"""
Application configuration settings.

Uses Pydantic Settings for type-safe configuration management.
All configuration comes from environment variables.
"""
from typing import Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    app_name: str = Field(default="AgentGuard", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="Number of API workers")
    api_reload: bool = Field(default=True, description="Auto-reload on code changes")

    # Frontend
    frontend_url: str = Field(default="http://localhost:3000", description="Frontend URL")

    # Database
    database_url: str = Field(..., description="PostgreSQL connection URL")
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_max_overflow: int = Field(default=10, description="Max overflow connections")
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    test_database_url: Optional[str] = Field(default=None, description="Test database URL")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_max_connections: int = Field(default=10, description="Max Redis connections")

    # Security
    secret_key: str = Field(..., description="Secret key for signing")
    encryption_key: str = Field(..., description="Encryption key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(default=60, description="JWT expiration time")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")

    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format: json or text")

    # Request Limits
    max_request_size_mb: int = Field(default=10, description="Max request size in MB")
    max_response_size_mb: int = Field(default=10, description="Max response size in MB")
    max_execution_timeout_seconds: int = Field(default=300, description="Max execution timeout")
    request_timeout_seconds: int = Field(default=30, description="Request timeout")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, description="Requests per minute")

    # Security - SSRF Protection
    block_private_networks: bool = Field(default=True, description="Block private IP ranges")
    block_localhost: bool = Field(default=True, description="Block localhost")
    block_metadata_endpoints: bool = Field(default=True, description="Block cloud metadata endpoints")
    allowed_domains: list[str] = Field(default=[], description="Explicitly allowed domains")

    # Observability
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")
    trace_sample_rate: float = Field(default=0.1, description="Trace sampling rate")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("allowed_domains", mode="before")
    @classmethod
    def parse_allowed_domains(cls, v: str | list[str]) -> list[str]:
        """Parse allowed domains from comma-separated string or list."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [domain.strip() for domain in v.split(",") if domain.strip()]
        return v

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        """Reject combinations that would weaken browser-origin protection."""
        if self.cors_allow_credentials and "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS cannot contain '*' when CORS_ALLOW_CREDENTIALS is enabled")
        if self.is_production and self.api_reload:
            raise ValueError("API_RELOAD must be disabled in production")
        return self

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"

    @property
    def max_request_size_bytes(self) -> int:
        """Get max request size in bytes."""
        return self.max_request_size_mb * 1024 * 1024

    @property
    def max_response_size_bytes(self) -> int:
        """Get max response size in bytes."""
        return self.max_response_size_mb * 1024 * 1024


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings singleton (useful for testing)."""
    global _settings
    _settings = None
