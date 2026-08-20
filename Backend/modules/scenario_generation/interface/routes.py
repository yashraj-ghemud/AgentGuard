"""
Scenario Generation Interface - REST API Routes

API endpoints for scenario generation and management.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database.base import get_db
from modules.scenario_generation.application.service import ScenarioGenerationService
from modules.scenario_generation.domain.schemas import (
    CreateScenarioSuiteRequest,
    ScenarioSuiteResponse,
    ScenarioResponse,
    GenerationRunResponse,
)
from modules.test_strategy.domain.models import TestStrategy
from modules.agent_intelligence.domain.models import AgentCapabilityProfile
from modules.risk_analysis.domain.models import RiskProfile


router = APIRouter(prefix="/api/v1", tags=["Scenario Generation"])


# ============================================================================
# Dependencies
# ============================================================================

def get_scenario_service(db: Session = Depends(get_db)) -> ScenarioGenerationService:
    """Get scenario generation service instance."""
    return ScenarioGenerationService(db=db)


# ============================================================================
# Scenario Suite Endpoints
# ============================================================================

@router.post("/agents/{agent_id}/scenario-suites", response_model=ScenarioSuiteResponse)
async def create_scenario_suite(
    agent_id: UUID,
    request: CreateScenarioSuiteRequest,
    db: Session = Depends(get_db),
    service: ScenarioGenerationService = Depends(get_scenario_service)
):
    """
    Generate a new scenario suite for an agent.
    
    This endpoint starts the scenario generation process using the specified
    test strategy. Generation happens synchronously (may take 30-60 seconds).
    
    Process:
    1. Fetch test strategy (or use default)
    2. Fetch capability and risk profiles
    3. Generate scenarios using LLM
    4. Save to database
    5. Return completed suite
    """
    # Validate agent_id matches request
    if agent_id != request.agent_id:
        raise HTTPException(status_code=400, detail="Agent ID mismatch")
    
    # Get agent version
    agent_version_id = request.agent_version_id
    if not agent_version_id:
        # TODO: Get latest version from agent registry
        raise HTTPException(status_code=400, detail="agent_version_id is required")
    
    # Get test strategy
    test_strategy = None
    if request.test_strategy_id:
        test_strategy = db.query(TestStrategy).filter(
            TestStrategy.id == request.test_strategy_id
        ).first()
        if not test_strategy:
            raise HTTPException(status_code=404, detail="Test strategy not found")
    else:
        # Get or create default strategy
        # For MVP, require explicit test_strategy_id
        raise HTTPException(status_code=400, detail="test_strategy_id is required")
    
    # Get capability profile (optional)
    capability_profile = db.query(AgentCapabilityProfile).filter(
        AgentCapabilityProfile.agent_id == agent_id,
        AgentCapabilityProfile.version_id == agent_version_id
    ).first()
    
    # Get risk profile (optional)
    risk_profile = db.query(RiskProfile).filter(
        RiskProfile.agent_id == agent_id
    ).first()
    
    # Generate scenarios
    try:
        suite = await service.generate_scenarios(
            agent_id=agent_id,
            agent_version_id=agent_version_id,
            test_strategy=test_strategy,
            capability_profile=capability_profile,
            risk_profile=risk_profile,
            suite_name=request.name,
            suite_description=None
        )
        
        return ScenarioSuiteResponse.model_validate(suite)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario generation failed: {str(e)}")


@router.get("/agents/{agent_id}/scenario-suites", response_model=List[ScenarioSuiteResponse])
def list_scenario_suites(
    agent_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ScenarioGenerationService = Depends(get_scenario_service)
):
    """
    List all scenario suites for an agent.
    
    Returns suites in reverse chronological order (newest first).
    """
    suites = service.repository.get_suites_by_agent(
        agent_id=agent_id,
        limit=limit,
        offset=offset
    )
    
    return [ScenarioSuiteResponse.model_validate(suite) for suite in suites]


@router.get("/scenario-suites/{suite_id}", response_model=ScenarioSuiteResponse)
def get_scenario_suite(
    suite_id: UUID,
    service: ScenarioGenerationService = Depends(get_scenario_service)
):
    """
    Get a specific scenario suite by ID.
    
    Returns suite metadata and statistics (not individual scenarios).
    """
    suite = service.get_suite(suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Scenario suite not found")
    
    return ScenarioSuiteResponse.model_validate(suite)


@router.post("/scenario-suites/{suite_id}/lock")
def lock_scenario_suite(
    suite_id: UUID,
    service: ScenarioGenerationService = Depends(get_scenario_service)
):
    """
    Lock a scenario suite to make it immutable.
    
    Once locked, scenarios cannot be modified or deleted.
    Used to preserve test suites for historical comparison.
    """
    success = service.repository.lock_suite(suite_id)
    if not success:
        raise HTTPException(status_code=404, detail="Suite not found or already locked")
    
    return {"message": "Suite locked successfully"}


@router.delete("/scenario-suites/{suite_id}")
def delete_scenario_suite(
    suite_id: UUID,
    service: ScenarioGenerationService = Depends(get_scenario_service)
):
    """
    Delete a scenario suite (only if unlocked).
    
    Deletes the suite and all its scenarios.
    """
    success = service.repository.delete_suite(suite_id)
    if not success:
        raise HTTPException(status_code=400, detail="Suite not found or is locked")
    
    return {"message": "Suite deleted successfully"}


# ============================================================================
# Scenario Endpoints
# ============================================================================

@router.get("/scenario-suites/{suite_id}/scenarios", response_model=List[ScenarioResponse])
def list_suite_scenarios(
    suite_id: UUID,
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(500, ge=1, le=1000),
    service: ScenarioGenerationService = Depends(get_scenario_service)
):
    """
    List all scenarios in a suite with optional filters.
    
    Scenarios are ordered by priority, then creation time.
    """
    scenarios = service.get_suite_scenarios(
        suite_id=suite_id,
        category=category,
        priority=priority,
        limit=limit
    )
    
    return [ScenarioResponse.model_validate(scenario) for scenario in scenarios]


@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(
    scenario_id: UUID,
    service: ScenarioGenerationService = Depends(get_scenario_service)
):
    """
    Get a specific scenario by ID.
    
    Returns full scenario details including conversation steps,
    expected behaviors, and validation rules.
    """
    scenario = service.repository.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return ScenarioResponse.model_validate(scenario)


# ============================================================================
# Generation Run Endpoints
# ============================================================================

@router.get("/agents/{agent_id}/generation-runs", response_model=List[GenerationRunResponse])
def list_generation_runs(
    agent_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    service: ScenarioGenerationService = Depends(get_scenario_service)
):
    """
    List all generation runs for an agent.
    
    Returns runs in reverse chronological order (newest first).
    Useful for tracking generation history and costs.
    """
    runs = service.repository.get_generation_runs_by_agent(
        agent_id=agent_id,
        limit=limit
    )
    
    return [GenerationRunResponse.model_validate(run) for run in runs]


@router.get("/generation-runs/{run_id}", response_model=GenerationRunResponse)
def get_generation_run(
    run_id: UUID,
    service: ScenarioGenerationService = Depends(get_scenario_service)
):
    """
    Get a specific generation run by ID.
    
    Returns progress, status, timing, and cost information.
    """
    run = service.get_generation_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Generation run not found")
    
    return GenerationRunResponse.model_validate(run)
