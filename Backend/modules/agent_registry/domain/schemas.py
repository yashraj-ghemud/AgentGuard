"""
Agent Registry domain schemas.

Pydantic models for validation and serialization.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field, HttpUrl, field_validator


class ExecutionMode(str, Enum):
    """Agent execution modes."""
    HTTP = "http"
    SDK = "sdk"
    BROWSER = "browser"


class RiskProfile(BaseModel):
    """Agent risk profile configuration."""
    risk_level: str = Field(default="medium", description="Risk level: low, medium, high, critical")
    requires_human_approval: bool = Field(default=False, description="Requires human approval")
    max_execution_time_seconds: int = Field(default=300, ge=1, le=3600, description="Max execution time")
    allowed_failure_rate: float = Field(default=0.1, ge=0.0, le=1.0, description="Allowed failure rate")
    
    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """Validate risk level."""
        allowed = {"low", "medium", "high", "critical"}
        if v.lower() not in allowed:
            raise ValueError(f"Risk level must be one of: {', '.join(allowed)}")
        return v.lower()


class AgentBase(BaseModel):
    """Base agent schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    endpoint_url: str = Field(..., description="Agent execution endpoint")
    execution_mode: ExecutionMode = Field(..., description="Execution mode")
    purpose: Optional[str] = Field(None, description="Agent purpose/use case")
    risk_profile: Optional[RiskProfile] = Field(default_factory=RiskProfile, description="Risk configuration")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
        validation_alias=AliasChoices("agent_metadata", "metadata"),
    )
    workspace_id: Optional[UUID] = Field(None, description="Workspace ID")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate agent name."""
        if not v.strip():
            raise ValueError("Agent name cannot be empty")
        # Allow alphanumeric, spaces, hyphens, underscores
        import re
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", v):
            raise ValueError("Agent name can only contain letters, numbers, spaces, hyphens, and underscores")
        return v.strip()

    @field_validator("endpoint_url")
    @classmethod
    def validate_endpoint_url(cls, v: str) -> str:
        """Validate endpoint URL format."""
        if not v.strip():
            raise ValueError("Endpoint URL cannot be empty")
        # Basic URL validation
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Endpoint URL must start with http:// or https://")
        return v


class CreateAgentRequest(AgentBase):
    """Request schema for creating an agent."""
    pass


class UpdateAgentRequest(BaseModel):
    """Request schema for updating an agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    purpose: Optional[str] = None
    risk_profile: Optional[RiskProfile] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate agent name if provided."""
        if v is not None:
            if not v.strip():
                raise ValueError("Agent name cannot be empty")
            import re
            if not re.match(r"^[a-zA-Z0-9\s\-_]+$", v):
                raise ValueError("Agent name can only contain letters, numbers, spaces, hyphens, and underscores")
            return v.strip()
        return v


class AgentResponse(AgentBase):
    """Response schema for agent data."""
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentFilters(BaseModel):
    """Filters for agent queries."""
    name: Optional[str] = Field(None, description="Filter by name (partial match)")
    execution_mode: Optional[ExecutionMode] = Field(None, description="Filter by execution mode")
    status: Optional[str] = Field(None, description="Filter by status")
    workspace_id: Optional[UUID] = Field(None, description="Filter by workspace")
