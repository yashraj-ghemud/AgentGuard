"""
Scenario Generation Domain Models

Database models for scenarios, suites, and generation runs.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Text, ForeignKey, Integer, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from core.database.base import Base


class ScenarioSuite(Base):
    """
    Collection of test scenarios for an agent.
    
    Immutable after execution starts.
    """
    __tablename__ = "scenario_suites"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(PG_UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    agent_version_id = Column(PG_UUID(as_uuid=True), ForeignKey("agent_versions.id", ondelete="CASCADE"), nullable=False)
    test_strategy_id = Column(PG_UUID(as_uuid=True), ForeignKey("test_strategies.id", ondelete="SET NULL"), nullable=True)
    
    # Suite metadata
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    suite_type = Column(String(50), nullable=False)  # baseline, adversarial, safety, regression, full
    
    # Statistics
    total_scenarios = Column(Integer, nullable=False, default=0)
    category_counts = Column(JSONB, nullable=False, default=dict)  # {normal: 10, edge: 5, ...}
    priority_counts = Column(JSONB, nullable=False, default=dict)
    risk_counts = Column(JSONB, nullable=False, default=dict)
    
    # Coverage
    tool_coverage = Column(JSONB, nullable=False, default=dict)  # per-tool coverage %
    coverage_score = Column(Float, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="draft")  # draft, generating, completed, failed
    generation_started_at = Column(DateTime, nullable=True)
    generation_completed_at = Column(DateTime, nullable=True)
    generation_error = Column(Text, nullable=True)
    
    # Immutability
    is_locked = Column(Boolean, nullable=False, default=False)
    locked_at = Column(DateTime, nullable=True)
    
    # Metadata
    generator_version = Column(String(50), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", backref="scenario_suites")
    agent_version = relationship("AgentVersion", backref="scenario_suites")
    test_strategy = relationship("TestStrategy", backref="scenario_suites")
    scenarios = relationship("Scenario", back_populates="suite", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ScenarioSuite(id={self.id}, name='{self.name}', total={self.total_scenarios}, status={self.status})>"


class Scenario(Base):
    """
    Individual test scenario for an agent.
    
    Contains user input, expected behavior, and validation rules.
    """
    __tablename__ = "scenarios"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    scenario_suite_id = Column(PG_UUID(as_uuid=True), ForeignKey("scenario_suites.id", ondelete="CASCADE"), nullable=True)
    agent_version_id = Column(PG_UUID(as_uuid=True), ForeignKey("agent_versions.id", ondelete="CASCADE"), nullable=False)
    
    # Classification
    category = Column(String(50), nullable=False)  # from ScenarioCategory enum
    subtype = Column(String(100), nullable=True)
    
    # Content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False)  # easy, medium, hard, expert
    priority = Column(String(20), nullable=False)  # low, medium, high, critical
    risk_level = Column(String(20), nullable=False)
    
    # Scenario data
    user_input = Column(Text, nullable=False)
    conversation_steps = Column(JSONB, nullable=False, default=list)  # array of turn objects
    preconditions = Column(JSONB, nullable=False, default=dict)
    environment_requirements = Column(JSONB, nullable=False, default=dict)
    
    # Expected behavior (structured)
    expected_behavior = Column(JSONB, nullable=False)  # array of expectation objects
    validation_rules = Column(JSONB, nullable=False)  # array of validation rule objects
    
    # Targeting
    target_tools = Column(JSONB, nullable=False, default=list)  # array of tool names
    tags = Column(JSONB, nullable=False, default=list)  # array of tag strings
    
    # Quality metadata
    quality_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    is_duplicate = Column(Boolean, nullable=False, default=False)
    duplicate_of_id = Column(PG_UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=True)
    
    # Generation metadata
    generated_by = Column(String(100), nullable=False)  # generator name
    generator_version = Column(String(50), nullable=False)
    generation_run_id = Column(PG_UUID(as_uuid=True), nullable=True)
    model_used = Column(String(100), nullable=False)
    
    # Status
    status = Column(String(20), nullable=False, default="draft")  # draft, validated, approved, rejected
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    suite = relationship("ScenarioSuite", back_populates="scenarios")
    agent_version = relationship("AgentVersion", backref="scenarios")
    duplicate_of = relationship("Scenario", remote_side=[id], backref="duplicates")

    def __repr__(self) -> str:
        return f"<Scenario(id={self.id}, title='{self.title[:50]}...', category={self.category}, priority={self.priority})>"


class ScenarioGenerationRun(Base):
    """
    Tracks a scenario generation job.
    
    Provides progress tracking and error reporting.
    """
    __tablename__ = "scenario_generation_runs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(PG_UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    scenario_suite_id = Column(PG_UUID(as_uuid=True), ForeignKey("scenario_suites.id", ondelete="CASCADE"), nullable=True)
    
    # Configuration
    requested_count = Column(Integer, nullable=False)
    strategy_config = Column(JSONB, nullable=False)
    
    # Progress
    status = Column(String(30), nullable=False, default="queued")  # queued, analyzing, generating, validating, etc.
    current_phase = Column(String(50), nullable=True)
    scenarios_generated = Column(Integer, nullable=False, default=0)
    scenarios_validated = Column(Integer, nullable=False, default=0)
    scenarios_rejected = Column(Integer, nullable=False, default=0)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)
    
    # Resource tracking
    total_llm_calls = Column(Integer, nullable=False, default=0)
    estimated_cost = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", backref="generation_runs")
    scenario_suite = relationship("ScenarioSuite", backref="generation_runs")

    def __repr__(self) -> str:
        return f"<ScenarioGenerationRun(id={self.id}, status={self.status}, generated={self.scenarios_generated}/{self.requested_count})>"
