"""Configuration security invariant tests."""

import pytest
from pydantic import ValidationError

from core.config.settings import Settings


def make_settings(**overrides):
    data = {
        "database_url": "postgresql://agentguard:agentguard@localhost/agentguard",
        "secret_key": "test-secret",
        "encryption_key": "test-encryption",
    }
    data.update(overrides)
    return Settings(**data)


def test_wildcard_cors_with_credentials_is_rejected():
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        make_settings(cors_origins=["*"], cors_allow_credentials=True)


def test_production_reload_is_rejected():
    with pytest.raises(ValidationError, match="API_RELOAD"):
        make_settings(app_env="production", api_reload=True)


def test_production_can_disable_reload():
    settings = make_settings(app_env="production", api_reload=False, cors_origins=["https://console.example.com"])
    assert settings.is_production is True
