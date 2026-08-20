"""
Agent Registry domain models.

Database models for the Agent Registry module.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, String, Text, Enum as SQLEnum, Index, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from core.database.base import BaseModel
from shared.types import EntityStatus


class Agent(BaseModel):
    """
    Agent database model.
    
    Represents an AI agent with its configuration and metadata.
    Each agent is uniquely identified and can have multiple versions.
    """
    __tablename__ = "agents"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    endpoint_url = Column(Text, nullable=False)
    execution_mode = Column(String(50), nullable=False)  # http, sdk, browser
    purpose = Column(Text)
    status = Column(
        SQLEnum(EntityStatus, name="entity_status"),
        nullable=False,
        default=EntityStatus.ACTIVE,
        server_default=text(f"'{EntityStatus.ACTIVE.value}'"),
    )
    risk_profile = Column(JSONB, default=dict)
    agent_metadata = Column("metadata", JSONB, default=dict)
    workspace_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_agents_name", "name"),
        Index("idx_agents_status", "status"),
        Index("idx_agents_workspace_id", "workspace_id"),
        Index("idx_agents_execution_mode", "execution_mode"),
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, status={self.status})>"
