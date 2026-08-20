"""
Agent Versioning domain models.

Database models for immutable agent version snapshots.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, String, Text, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from core.database.base import BaseModel


class AgentVersion(BaseModel):
    """
    Agent Version model - immutable snapshot of agent configuration.
    
    Each version captures the complete state of an agent at a specific point in time.
    Versions are immutable - once created, they cannot be modified.
    """
    __tablename__ = "agent_versions"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    agent_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number = Column(String(100), nullable=False)
    snapshot = Column(JSONB, nullable=False)  # Complete agent configuration snapshot
    notes = Column(Text)
    snapshot_metadata = Column(JSONB, default=dict)

    # Relationship to agent (for eager loading)
    # Note: We don't define back_populates to avoid tight coupling
    # agent = relationship("Agent")

    # Indexes and constraints
    __table_args__ = (
        Index("idx_agent_versions_agent_id", "agent_id"),
        Index("idx_agent_versions_created_at", "created_at"),
        UniqueConstraint("agent_id", "version_number", name="uk_agent_versions_agent_version"),
    )

    def __repr__(self) -> str:
        return f"<AgentVersion(id={self.id}, agent_id={self.agent_id}, version={self.version_number})>"
