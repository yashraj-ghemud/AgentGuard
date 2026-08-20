"""
Test Strategy Interface - REST API Routes

API endpoints for test strategy planning.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database.base import get_db
from modules.test_strategy.application.service import TestStrategyService
from modules.test_strategy.domain.models import TestStrategy
from modules.agent_intelligence.domain.models import AgentCapabilityProfile
from modules.risk_analysis.domain.models import RiskProfile


router = APIRouter(prefix="/api/v1", tags=["Test Strategy"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any


class CreateTestStrategyRequest(BaseModel):
    """Request to create a test strategy."""
    agent_id: UUID
    capability_profile_id: Optional[UUID] = None
    risk_profile_id: Optional[UUID] = None
    name: Optional[str] = None
    description: Optional[str] = None
    custom_distribution: Optional[Dict[str, int]] = Field(
        None,
        description="Custom category distribution (percentages)"
    )
    custom_scenario_count: Optional[int] = Field(
        None,
        ge=10,
        le=500,
        description="Custom total scenario count"
    )


class TestStrategyResponse(BaseModel):
    """Test strategy response."""
    id: UUID
    agent_id: UUID
    capability_profile_id: Optional[UUID]
    risk_profile_id: Optional[UUID]
    
    name: str
    description: Optional[str]
    
    category_distribution: Dict[str, int]
    total_scenario_count: int
    multi_turn_percentage: int
    
    tool_coverage_targets: Dict[str, int]
    risk_coverage_targets: Dict[str, Any]
    
    model_used: Optional[str]
    generator_version: str
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Dependencies
# ============================================================================

def get_test_strategy_service(db: Session = Depends(get_db)) -> TestStrategyService:
    """Get test strategy service instance."""
    return TestStrategyService(db=db)


# ============================================================================
# Test Strategy Endpoints
# ============================================================================

@router.post("/agents/{agent_id}/test-strategies", response_model=TestStrategyResponse)
def create_test_strategy(
    agent_id: UUID,
    request: CreateTestStrategyRequest,
    db: Session = Depends(get_db),
    service: TestStrategyService = Depends(get_test_strategy_service)
):
    """
    Create a test strategy for an agent.
    
    This endpoint creates a test strategy based on the agent's capabilities
    and risk profile. The strategy determines how many scenarios to generate
    for each category.
    
    Process:
    1. Fetch capability profile (optional)
    2. Fetch risk profile (required for intelligent planning)
    3. Calculate category distribution based on risk level
    4. Set tool coverage targets based on tool risk levels
    5. Save strategy to database
    
    If custom_distribution is provided, it overrides the calculated distribution.
    """
    # Validate agent_id matches request
    if agent_id != request.agent_id:
        raise HTTPException(status_code=400, detail="Agent ID mismatch")
    
    # Get capability profile (optional)
    capability_profile = None
    if request.capability_profile_id:
        capability_profile = db.query(AgentCapabilityProfile).filter(
            AgentCapabilityProfile.id == request.capability_profile_id
        ).first()
        if not capability_profile:
            raise HTTPException(status_code=404, detail="Capability profile not found")
    
    # Get risk profile (recommended)
    risk_profile = None
    if request.risk_profile_id:
        risk_profile = db.query(RiskProfile).filter(
            RiskProfile.id == request.risk_profile_id
        ).first()
        if not risk_profile:
            raise HTTPException(status_code=404, detail="Risk profile not found")
    
    # Create strategy
    try:
        strategy = service.create_test_strategy(
            agent_id=agent_id,
            capability_profile=capability_profile,
            risk_profile=risk_profile,
            custom_name=request.name,
            custom_description=request.description,
            custom_distribution=request.custom_distribution,
            custom_scenario_count=request.custom_scenario_count
        )
        
        return TestStrategyResponse.model_validate(strategy)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy creation failed: {str(e)}")


@router.get("/agents/{agent_id}/test-strategies", response_model=list[TestStrategyResponse])
def list_test_strategies(
    agent_id: UUID,
    db: Session = Depends(get_db)
):
    """
    List all test strategies for an agent.
    
    Returns strategies in reverse chronological order (newest first).
    """
    strategies = db.query(TestStrategy).filter(
        TestStrategy.agent_id == agent_id
    ).order_by(TestStrategy.created_at.desc()).all()
    
    return [TestStrategyResponse.model_validate(strategy) for strategy in strategies]


@router.get("/test-strategies/{strategy_id}", response_model=TestStrategyResponse)
def get_test_strategy(
    strategy_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific test strategy by ID.
    
    Returns the complete strategy configuration including category
    distribution and coverage targets.
    """
    strategy = db.query(TestStrategy).filter(TestStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Test strategy not found")
    
    return TestStrategyResponse.model_validate(strategy)


@router.delete("/test-strategies/{strategy_id}")
def delete_test_strategy(
    strategy_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a test strategy.
    
    Note: This will cascade delete any scenario suites that reference
    this strategy (via ON DELETE CASCADE).
    """
    strategy = db.query(TestStrategy).filter(TestStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Test strategy not found")
    
    db.delete(strategy)
    db.commit()
    
    return {"message": "Test strategy deleted successfully"}


@router.get("/agents/{agent_id}/test-strategies/recommended", response_model=TestStrategyResponse)
def get_recommended_strategy(
    agent_id: UUID,
    db: Session = Depends(get_db),
    service: TestStrategyService = Depends(get_test_strategy_service)
):
    """
    Get the recommended test strategy for an agent.
    
    This endpoint calculates the optimal strategy based on the agent's
    most recent risk profile without saving it to the database.
    
    Useful for previewing what strategy would be recommended before
    actually creating it.
    """
    # Get latest risk profile
    risk_profile = db.query(RiskProfile).filter(
        RiskProfile.agent_id == agent_id
    ).order_by(RiskProfile.created_at.desc()).first()
    
    if not risk_profile:
        raise HTTPException(
            status_code=404,
            detail="No risk profile found. Analyze agent risk first."
        )
    
    # Get latest capability profile (optional)
    capability_profile = db.query(AgentCapabilityProfile).filter(
        AgentCapabilityProfile.agent_id == agent_id
    ).order_by(AgentCapabilityProfile.created_at.desc()).first()
    
    # Calculate recommended strategy (without saving)
    distribution = service._calculate_category_distribution(risk_profile)
    tool_coverage = service._calculate_tool_coverage_targets(capability_profile, risk_profile)
    risk_coverage = service._calculate_risk_coverage_targets(risk_profile)
    
    # Create response object (not saved to DB)
    from uuid import uuid4
    strategy_preview = TestStrategy(
        id=uuid4(),
        agent_id=agent_id,
        capability_profile_id=capability_profile.id if capability_profile else None,
        risk_profile_id=risk_profile.id,
        name=f"Recommended Strategy (Preview)",
        description=f"Recommended strategy based on {risk_profile.overall_risk} risk profile",
        category_distribution=distribution,
        total_scenario_count=risk_profile.recommended_scenario_count,
        multi_turn_percentage=30,
        tool_coverage_targets=tool_coverage,
        risk_coverage_targets=risk_coverage,
        model_used=None,
        generator_version=service.GENERATOR_VERSION
    )
    
    return TestStrategyResponse.model_validate(strategy_preview)
