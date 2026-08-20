"""
Scenario Generation Domain Schemas

Pydantic schemas for scenario generation and validation.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from shared.scenario_types import (
    ScenarioCategory,
    ExpectedBehaviorType,
    DifficultyLevel,
    PriorityLevel,
    ScenarioStatus,
    SuiteType,
    SuiteStatus,
    GenerationRunStatus,
)


# ============================================================================
# Scenario Components (LLM-generated structures)
# ============================================================================

class ConversationTurn(BaseModel):
    """A single turn in a multi-turn scenario."""
    turn_number: int = Field(..., ge=1, description="Turn number")
    speaker: str = Field(..., description="user or agent")
    message: str = Field(..., description="Message content")
    expected_agent_action: Optional[str] = Field(None, description="What agent should do")


class ExpectedBehavior(BaseModel):
    """Expected behavior for a scenario."""
    behavior_type: ExpectedBehaviorType = Field(..., description="Type of expected behavior")
    description: str = Field(..., description="Description of expected behavior")
    tool_name: Optional[str] = Field(None, description="Specific tool if applicable")
    must_not_contain: Optional[List[str]] = Field(None, description="Phrases agent must not say")


class ValidationRule(BaseModel):
    """Validation rule for scenario evaluation."""
    rule_type: str = Field(..., description="Type of validation rule")
    condition: str = Field(..., description="Condition to check")
    expected_value: Optional[Any] = Field(None, description="Expected value")
    failure_message: str = Field(..., description="Message if validation fails")


class GeneratedScenario(BaseModel):
    """
    LLM-generated scenario structure.
    
    Used for structured output from LLM.
    """
    title: str = Field(..., max_length=500, description="Scenario title")
    description: str = Field(..., description="What this scenario tests")
    category: ScenarioCategory = Field(..., description="Scenario category")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    priority: PriorityLevel = Field(..., description="Test priority")
    risk_level: str = Field(..., description="Risk level")
    
    # Scenario content
    user_input: str = Field(..., description="Initial user input")
    conversation_steps: List[ConversationTurn] = Field(
        default_factory=list,
        description="Multi-turn conversation steps"
    )
    
    # Expected outcomes
    expected_behavior: List[ExpectedBehavior] = Field(..., description="Expected behaviors")
    validation_rules: List[ValidationRule] = Field(..., description="Validation rules")
    
    # Targeting
    target_tools: List[str] = Field(default_factory=list, description="Tools this tests")
    tags: List[str] = Field(default_factory=list, description="Tags for filtering")
    
    # Quality
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Self-assessed quality")
    rationale: Optional[str] = Field(None, description="Why this scenario is valuable")


class GeneratedScenarioBatch(BaseModel):
    """Provider-compatible wrapper for a list of generated scenarios."""

    scenarios: List[GeneratedScenario] = Field(default_factory=list)


# ============================================================================
# API Schemas
# ============================================================================

class CreateScenarioSuiteRequest(BaseModel):
    """Request to create a scenario suite."""
    agent_id: UUID
    agent_version_id: Optional[UUID] = None
    name: str = Field(..., max_length=200)
    suite_type: SuiteType
    scenario_count: int = Field(..., ge=10, le=500)
    test_strategy_id: Optional[UUID] = None
    custom_distribution: Optional[Dict[str, int]] = None


class ScenarioSuiteResponse(BaseModel):
    """Scenario suite response."""
    id: UUID
    agent_id: UUID
    agent_version_id: UUID
    test_strategy_id: Optional[UUID]
    
    name: str
    description: Optional[str]
    suite_type: str
    
    total_scenarios: int
    category_counts: Dict[str, int]
    priority_counts: Dict[str, int]
    risk_counts: Dict[str, int]
    
    tool_coverage: Dict[str, Any]
    coverage_score: Optional[float]
    
    status: str
    is_locked: bool
    
    generator_version: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScenarioResponse(BaseModel):
    """Scenario response."""
    id: UUID
    scenario_suite_id: Optional[UUID]
    agent_version_id: UUID
    
    category: str
    subtype: Optional[str]
    
    title: str
    description: str
    difficulty: str
    priority: str
    risk_level: str
    
    user_input: str
    conversation_steps: List[Dict[str, Any]]
    expected_behavior: List[Dict[str, Any]]
    validation_rules: List[Dict[str, Any]]
    
    target_tools: List[str]
    tags: List[str]
    
    quality_score: Optional[float]
    relevance_score: Optional[float]
    is_duplicate: bool
    
    status: str
    
    created_at: datetime

    class Config:
        from_attributes = True


class GenerationRunResponse(BaseModel):
    """Generation run response."""
    id: UUID
    agent_id: UUID
    scenario_suite_id: Optional[UUID]
    
    requested_count: int
    status: str
    current_phase: Optional[str]
    
    scenarios_generated: int
    scenarios_validated: int
    scenarios_rejected: int
    
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    
    error_message: Optional[str]
    
    total_llm_calls: int
    estimated_cost: Optional[float]
    
    created_at: datetime

    class Config:
        from_attributes = True
