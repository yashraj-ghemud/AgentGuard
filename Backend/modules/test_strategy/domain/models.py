"""
Test Strategy Domain Models

Database models for test strategies.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from core.database.base import Base


class TestStrategy(Base):
    """
    Test strategy for an agent.
    
    Defines how to test an agent based on its capabilities and risks.
    """
    __tablename__ = "test_strategies"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(PG_UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    capability_profile_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_capability_profiles.id", ondelete="CASCADE"),
        nullable=True
    )
    risk_profile_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("risk_profiles.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Strategy metadata
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Category distribution (percentages must sum to ~100)
    category_distribution = Column(JSONB, nullable=False)  # {normal: 20, edge: 15, ...}
    
    # Overall scenario count
    total_scenario_count = Column(Integer, nullable=False)
    
    # Multi-turn testing
    multi_turn_percentage = Column(Integer, nullable=False)  # 0-100
    
    # Coverage targets
    tool_coverage_targets = Column(JSONB, nullable=False, default=dict)  # per-tool scenario counts
    risk_coverage_targets = Column(JSONB, nullable=False, default=dict)  # per-risk-level counts
    
    # Generation metadata
    model_used = Column(String(100), nullable=True)
    generator_version = Column(String(50), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", backref="test_strategies")
    capability_profile = relationship("AgentCapabilityProfile", backref="test_strategies")
    risk_profile = relationship("RiskProfile", backref="test_strategies")

    def __repr__(self) -> str:
        return f"<TestStrategy(id={self.id}, name='{self.name}', agent_id={self.agent_id}, total={self.total_scenario_count})>"
