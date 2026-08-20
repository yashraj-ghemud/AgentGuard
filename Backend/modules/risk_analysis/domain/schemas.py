"""
Risk Analysis Domain Schemas

Pydantic schemas for risk assessment.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from shared.scenario_types import OverallRisk, TestIntensity


# ============================================================================
# LLM-Generated Structures
# ============================================================================

class ToolRiskAssessment(BaseModel):
    """Risk assessment for a specific tool."""
    tool_name: str = Field(..., description="Tool name")
    declared_risk_level: str = Field(..., description="Risk level from tool metadata")
    assessed_risk_level: str = Field(..., description="Actual assessed risk level")
    risk_factors: List[str] = Field(default_factory=list, description="Specific risk factors")
    mitigation_strategies: List[str] = Field(default_factory=list, description="How to mitigate risks")
    requires_confirmation: bool = Field(..., description="Should require user confirmation")


class UnsafeOperation(BaseModel):
    """Description of an unsafe operation."""
    operation: str = Field(..., description="Operation name")
    risk_level: str = Field(..., description="Risk level")
    consequences: str = Field(..., description="Potential consequences")
    tools_involved: List[str] = Field(default_factory=list, description="Tools used")
    reversible: bool = Field(..., description="Can operation be undone")


class RiskInconsistency(BaseModel):
    """Detected inconsistency between declared and actual risk."""
    tool_or_operation: str = Field(..., description="Tool or operation name")
    inconsistency_type: str = Field(..., description="Type of inconsistency")
    declared: str = Field(..., description="What metadata declares")
    actual: str = Field(..., description="What analysis reveals")
    severity: str = Field(..., description="Severity: low, medium, high")
    recommendation: str = Field(..., description="Recommended action")


class PriorityTestArea(BaseModel):
    """High-priority area for testing."""
    area: str = Field(..., description="Test area name")
    priority: str = Field(..., description="Priority: low, medium, high, critical")
    reason: str = Field(..., description="Why this is important to test")
    suggested_scenario_types: List[str] = Field(default_factory=list, description="Types of scenarios to generate")


class RiskScoreBreakdown(BaseModel):
    """Detailed risk scoring."""
    tool_risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk from tools")
    destructive_action_score: float = Field(..., ge=0.0, le=1.0, description="Risk from destructive actions")
    security_risk_score: float = Field(..., ge=0.0, le=1.0, description="Security vulnerability risk")
    failure_impact_score: float = Field(..., ge=0.0, le=1.0, description="Impact of potential failures")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall risk score")


class RiskAnalysisResult(BaseModel):
    """
    LLM-generated risk analysis.
    
    This is the structured output for risk assessment.
    """
    overall_risk: OverallRisk = Field(..., description="Overall risk level")
    
    high_risk_tools: List[ToolRiskAssessment] = Field(default_factory=list, description="High-risk tools")
    critical_tools: List[ToolRiskAssessment] = Field(default_factory=list, description="Critical tools")
    unsafe_operations: List[UnsafeOperation] = Field(default_factory=list, description="Unsafe operations")
    confirmation_required_operations: List[str] = Field(default_factory=list, description="Operations needing confirmation")
    
    risk_inconsistencies: List[RiskInconsistency] = Field(default_factory=list, description="Detected inconsistencies")
    
    recommended_test_intensity: TestIntensity = Field(..., description="Recommended test intensity")
    recommended_scenario_count: int = Field(..., ge=10, le=500, description="Recommended number of scenarios")
    
    priority_test_areas: List[PriorityTestArea] = Field(default_factory=list, description="Priority areas")
    
    risk_scores: RiskScoreBreakdown = Field(..., description="Risk score breakdown")


# ============================================================================
# API Schemas
# ============================================================================

class AnalyzeRiskRequest(BaseModel):
    """Request to analyze agent risk."""
    agent_id: UUID
    capability_profile_id: Optional[UUID] = None
    force_regenerate: bool = Field(default=False, description="Force regeneration even if cached")


class RiskProfileResponse(BaseModel):
    """Risk profile response."""
    id: UUID
    agent_id: UUID
    capability_profile_id: Optional[UUID]
    
    overall_risk: str
    
    high_risk_tools: List[Dict[str, Any]]
    critical_tools: List[Dict[str, Any]]
    unsafe_operations: List[Dict[str, Any]]
    confirmation_required_operations: List[str]
    
    risk_inconsistencies: List[Dict[str, Any]]
    
    recommended_test_intensity: str
    recommended_scenario_count: int
    
    priority_test_areas: List[Dict[str, Any]]
    
    risk_scores: Dict[str, float]
    
    model_used: Optional[str]
    generator_version: str
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
