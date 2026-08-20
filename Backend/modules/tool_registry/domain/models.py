"""
Tool Registry domain models.

Database models for tool definitions and agent-tool associations.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from core.database.base import BaseModel
from shared.types import EntityStatus


class Tool(BaseModel):
    """
    Tool database model.
    
    Represents a tool/function that an agent can use, with schema definitions
    and risk characteristics.
    """
    __tablename__ = "tools"

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
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    input_schema = Column(JSONB, nullable=False)
    output_schema = Column(JSONB)
    risk_level = Column(String(50), nullable=False)  # low, medium, high, critical
    is_destructive = Column(Boolean, nullable=False, default=False)
    is_reversible = Column(Boolean, nullable=False, default=True)
    requires_confirmation = Column(Boolean, nullable=False, default=False)
    timeout_seconds = Column(Integer)
    status = Column(String(50), nullable=False, default=EntityStatus.ACTIVE.value)
    tool_metadata = Column("metadata", JSONB, default=dict)

    # Indexes and constraints
    __table_args__ = (
        Index("idx_tools_agent_id", "agent_id"),
        Index("idx_tools_risk_level", "risk_level"),
        Index("idx_tools_status", "status"),
        UniqueConstraint("agent_id", "name", name="uk_tools_agent_name"),
    )

    def __repr__(self) -> str:
        return f"<Tool(id={self.id}, name={self.name}, agent_id={self.agent_id}, risk={self.risk_level})>"
