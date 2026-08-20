"""
Tool Registry domain schemas.

Pydantic models for validation and serialization.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field, field_validator

from shared.types import RiskLevel


class ToolBase(BaseModel):
    """Base tool schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Tool name")
    description: str = Field(..., min_length=1, max_length=5000, description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="JSON schema for tool inputs")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for tool outputs")
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    is_destructive: bool = Field(default=False, description="Whether tool modifies state")
    is_reversible: bool = Field(default=True, description="Whether action can be undone")
    requires_confirmation: bool = Field(default=False, description="Requires user approval")
    timeout_seconds: Optional[int] = Field(
        None,
        ge=1,
        le=3600,
        description="Max execution time in seconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
        validation_alias=AliasChoices("tool_metadata", "metadata"),
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tool name."""
        if not v.strip():
            raise ValueError("Tool name cannot be empty")
        # Allow alphanumeric, underscores, hyphens
        import re
        if not re.match(r"^[a-zA-Z0-9_\-]+$", v):
            raise ValueError("Tool name can only contain letters, numbers, underscores, and hyphens")
        return v.strip()

    @field_validator("input_schema")
    @classmethod
    def validate_input_schema(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input schema is valid JSON Schema."""
        if not v:
            raise ValueError("Input schema cannot be empty")
        
        # Basic JSON Schema validation
        if not isinstance(v, dict):
            raise ValueError("Input schema must be an object")
        
        # Must have type property
        if "type" not in v:
            raise ValueError("Input schema must have a 'type' property")
        
        return v

    @field_validator("output_schema")
    @classmethod
    def validate_output_schema(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate output schema if provided."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Output schema must be an object")
            if "type" not in v:
                raise ValueError("Output schema must have a 'type' property")
        return v


class RegisterToolRequest(ToolBase):
    """Request schema for registering a tool."""
    pass


class UpdateToolRequest(BaseModel):
    """Request schema for updating a tool."""
    description: Optional[str] = Field(None, min_length=1, max_length=5000)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    risk_level: Optional[RiskLevel] = None
    is_destructive: Optional[bool] = None
    is_reversible: Optional[bool] = None
    requires_confirmation: Optional[bool] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=3600)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("input_schema")
    @classmethod
    def validate_input_schema(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate input schema if provided."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Input schema must be an object")
            if "type" not in v:
                raise ValueError("Input schema must have a 'type' property")
        return v

    @field_validator("output_schema")
    @classmethod
    def validate_output_schema(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate output schema if provided."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Output schema must be an object")
            if "type" not in v:
                raise ValueError("Output schema must have a 'type' property")
        return v


class ToolResponse(ToolBase):
    """Response schema for tool data."""
    id: UUID
    agent_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolFilters(BaseModel):
    """Filters for tool queries."""
    risk_level: Optional[RiskLevel] = Field(None, description="Filter by risk level")
    is_destructive: Optional[bool] = Field(None, description="Filter by destructive flag")
    status: Optional[str] = Field(None, description="Filter by status")
