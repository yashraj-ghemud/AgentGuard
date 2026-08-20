"""Shared pytest configuration for isolated backend tests."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql://agentguard:agentguard@localhost/agentguard")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("API_RELOAD", "false")
