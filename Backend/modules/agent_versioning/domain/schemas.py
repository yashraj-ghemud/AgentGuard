"""
Agent Versioning domain schemas.

Pydantic models for validation and serialization.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CreateVersionRequest(BaseModel):
    """Request schema for creating an agent version."""
    version_number: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Version identifier (auto-generated if not provided)",
    )
    notes: Optional[str] = Field(
        None,
        max_length=5000,
        description="Version notes or changelog",
    )
    snapshot_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional snapshot metadata",
    )

    @field_validator("version_number")
    @classmethod
    def validate_version_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate version number format."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Version number cannot be empty")
            # Allow alphanumeric, dots, hyphens, underscores
            import re
            if not re.match(r"^[a-zA-Z0-9\.\-_]+$", v):
                raise ValueError(
                    "Version number can only contain letters, numbers, dots, hyphens, and underscores"
                )
            return v
        return v


class AgentSnapshotData(BaseModel):
    """Schema for agent snapshot data."""
    agent_id: UUID
    name: str
    description: Optional[str] = None
    endpoint_url: str
    execution_mode: str
    purpose: Optional[str] = None
    status: str
    risk_profile: Dict[str, Any]
    metadata: Dict[str, Any]
    workspace_id: Optional[UUID] = None
    captured_at: datetime
    # Tools associated at snapshot time
    tool_ids: list[UUID] = Field(default_factory=list)


class AgentVersionResponse(BaseModel):
    """Response schema for agent version data."""
    id: UUID
    agent_id: UUID
    version_number: str
    snapshot: AgentSnapshotData
    notes: Optional[str] = None
    snapshot_metadata: Dict[str, Any]
    created_at: datetime
    is_immutable: bool = Field(default=True, description="Versions are always immutable")

    class Config:
        from_attributes = True

    @classmethod
    def from_db_model(cls, version: Any) -> "AgentVersionResponse":
        """
        Create response from database model.
        
        Args:
            version: AgentVersion database model
            
        Returns:
            AgentVersionResponse instance
        """
        # Parse snapshot from JSONB
        snapshot_data = AgentSnapshotData(**version.snapshot)
        
        return cls(
            id=version.id,
            agent_id=version.agent_id,
            version_number=version.version_number,
            snapshot=snapshot_data,
            notes=version.notes,
            snapshot_metadata=version.snapshot_metadata,
            created_at=version.created_at,
            is_immutable=True,
        )


class AgentVersionSummary(BaseModel):
    """Abbreviated version information for list views."""
    id: UUID
    agent_id: UUID
    version_number: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
