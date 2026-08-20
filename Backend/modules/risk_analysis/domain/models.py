"""
Risk Analysis Domain Models

Database models for risk profiles.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Text, ForeignKey, Integer, Float, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from core.database.base import Base


class RiskProfile(Base):
    """
    Risk profile for an agent.
    
    Analyzes tools and operations to assess risk and recommend test strategy.
    """
    __tablename__ = "risk_profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(PG_UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    capability_profile_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_capability_profiles.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Overall risk assessment
    overall_risk = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Tool risk analysis
    high_risk_tools = Column(JSONB, nullable=False, default=list)  # array of tool risk objects
    critical_tools = Column(JSONB, nullable=False, default=list)
    unsafe_operations = Column(JSONB, nullable=False, default=list)
    confirmation_required_operations = Column(JSONB, nullable=False, default=list)
    
    # Risk inconsistencies (metadata vs actual behavior)
    risk_inconsistencies = Column(JSONB, nullable=False, default=list)
    
    # Test recommendations
    recommended_test_intensity = Column(String(20), nullable=False)  # light, moderate, thorough, exhaustive
    recommended_scenario_count = Column(Integer, nullable=False)
    
    # Priority areas for testing
    priority_test_areas = Column(JSONB, nullable=False, default=list)
    
    # Risk scoring breakdown
    risk_scores = Column(JSONB, nullable=False, default=dict)  # detailed risk scores per dimension
    
    # Generation metadata
    model_used = Column(String(100), nullable=True)  # Optional: may be rule-based
    generator_version = Column(String(50), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", backref="risk_profiles")
    capability_profile = relationship("AgentCapabilityProfile", backref="risk_profiles")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("agent_id", "capability_profile_id", name="uq_risk_agent_capability"),
    )

    def __repr__(self) -> str:
        return f"<RiskProfile(id={self.id}, agent_id={self.agent_id}, overall_risk={self.overall_risk})>"
