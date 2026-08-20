"""
Agent Intelligence Domain Schemas

Pydantic schemas for agent capability analysis.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


# ============================================================================
# LLM-Generated Structures (must be strict for validation)
# ============================================================================

class Capability(BaseModel):
    """A specific capability the agent has."""
    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="What this capability enables")
    tools_used: List[str] = Field(default_factory=list, description="Tools that enable this capability")


class ToolCapability(BaseModel):
    """Capability provided by a specific tool."""
    tool_name: str = Field(..., description="Tool name")
    capability: str = Field(..., description="What this tool enables the agent to do")
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")
    requires_confirmation: bool = Field(default=False, description="Whether tool requires user confirmation")


class OperationDescription(BaseModel):
    """Description of an operation."""
    operation: str = Field(..., description="Operation name")
    description: str = Field(..., description="What the operation does")
    tools_involved: List[str] = Field(default_factory=list, description="Tools used in operation")
    risk_reason: Optional[str] = Field(None, description="Why this operation is risky")


class AmbiguityPoint(BaseModel):
    """Point where user input might be ambiguous."""
    scenario: str = Field(..., description="Ambiguous scenario")
    clarification_needed: str = Field(..., description="What clarification is needed")
    example: Optional[str] = Field(None, description="Example of ambiguous input")


class FailureSurface(BaseModel):
    """Potential failure point."""
    surface: str = Field(..., description="Failure surface name")
    description: str = Field(..., description="How failure could occur")
    likelihood: str = Field(..., description="Likelihood: low, medium, high")
    impact: str = Field(..., description="Impact: low, medium, high, critical")


class SecuritySurface(BaseModel):
    """Security-sensitive area."""
    surface: str = Field(..., description="Security surface name")
    description: str = Field(..., description="Security concern")
    attack_vectors: List[str] = Field(default_factory=list, description="Possible attack vectors")


class AnalysisConfidence(BaseModel):
    """Confidence scores for analysis dimensions."""
    goal_understanding: float = Field(..., ge=0.0, le=1.0, description="Confidence in understanding agent's goal")
    capability_completeness: float = Field(..., ge=0.0, le=1.0, description="Confidence capabilities are complete")
    risk_assessment: float = Field(..., ge=0.0, le=1.0, description="Confidence in risk assessment")
    failure_coverage: float = Field(..., ge=0.0, le=1.0, description="Confidence failure surfaces are covered")
    overall: float = Field(..., ge=0.0, le=1.0, description="Overall analysis confidence")


class AgentCapabilityAnalysis(BaseModel):
    """
    LLM-generated analysis of agent capabilities.
    
    This is the structured output from the LLM that will be validated.
    """
    primary_goal: str = Field(..., description="Agent's main objective")
    secondary_goals: List[str] = Field(default_factory=list, description="Additional goals")
    
    capabilities: List[Capability] = Field(default_factory=list, description="Agent capabilities")
    domains: List[str] = Field(default_factory=list, description="Domains agent operates in")
    tool_capabilities: List[ToolCapability] = Field(default_factory=list, description="Tool-specific capabilities")
    
    high_risk_operations: List[OperationDescription] = Field(default_factory=list, description="High-risk operations")
    destructive_operations: List[OperationDescription] = Field(default_factory=list, description="Destructive operations")
    reversible_operations: List[OperationDescription] = Field(default_factory=list, description="Reversible operations")
    
    required_inputs: List[str] = Field(default_factory=list, description="Required user inputs")
    optional_inputs: List[str] = Field(default_factory=list, description="Optional user inputs")
    
    ambiguity_points: List[AmbiguityPoint] = Field(default_factory=list, description="Ambiguous scenarios")
    failure_surfaces: List[FailureSurface] = Field(default_factory=list, description="Potential failure points")
    security_surfaces: List[SecuritySurface] = Field(default_factory=list, description="Security concerns")
    
    assumptions: List[str] = Field(default_factory=list, description="Assumptions agent makes")
    constraints: List[str] = Field(default_factory=list, description="Agent constraints")
    
    confidence: AnalysisConfidence = Field(..., description="Confidence in analysis")


# ============================================================================
# API Schemas
# ============================================================================

class AnalyzeAgentRequest(BaseModel):
    """Request to analyze an agent."""
    agent_id: UUID
    version_id: Optional[UUID] = None
    force_regenerate: bool = Field(default=False, description="Force regeneration even if cached")
    custom_constraints: Optional[List[str]] = Field(None, description="Additional constraints to consider")


class AgentCapabilityProfileResponse(BaseModel):
    """Agent capability profile response."""
    id: UUID
    agent_id: UUID
    version_id: Optional[UUID]
    
    primary_goal: Optional[str]
    secondary_goals: List[str]
    
    capabilities: List[Dict[str, Any]]
    domains: List[str]
    tool_capabilities: List[Dict[str, Any]]
    
    high_risk_operations: List[Dict[str, Any]]
    destructive_operations: List[Dict[str, Any]]
    reversible_operations: List[Dict[str, Any]]
    
    required_inputs: List[str]
    optional_inputs: List[str]
    
    ambiguity_points: List[Dict[str, Any]]
    failure_surfaces: List[Dict[str, Any]]
    security_surfaces: List[Dict[str, Any]]
    
    assumptions: List[str]
    constraints: List[str]
    
    confidence: Dict[str, float]
    
    model_used: str
    generator_version: str
    generation_timestamp: datetime
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
