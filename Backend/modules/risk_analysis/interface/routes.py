"""
Risk Analysis API Routes

REST API endpoints for agent risk analysis.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database.base import get_db
from core.events.local_publisher import LocalEventPublisher
from modules.risk_analysis.application.service import RiskAnalysisService
from modules.risk_analysis.domain.schemas import RiskProfileResponse
from shared.exceptions import NotFoundError, InternalError

router = APIRouter(prefix="/api/v1/agents", tags=["risk-analysis"])


def get_service(db: Session = Depends(get_db)) -> RiskAnalysisService:
    """Dependency to get risk analysis service."""
    publisher = LocalEventPublisher()
    return RiskAnalysisService(db=db, event_publisher=publisher)


@router.post(
    "/{agent_id}/risk/analyze",
    response_model=RiskProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze agent risk",
    description="Analyze agent risk based on tools and capabilities"
)
async def analyze_risk(
    agent_id: UUID,
    capability_profile_id: Optional[UUID] = None,
    force_regenerate: bool = False,
    service: RiskAnalysisService = Depends(get_service)
):
    """
    Analyze agent risk profile.
    
    Examines:
    - Tool risk levels and capabilities
    - Destructive vs reversible operations
    - Security vulnerabilities
    - Potential for misuse
    - Failure impact
    
    Returns risk assessment with test recommendations.
    """
    try:
        profile = await service.analyze_risk(
            agent_id=agent_id,
            capability_profile_id=capability_profile_id,
            force_regenerate=force_regenerate
        )
        return service.to_response(profile)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InternalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{agent_id}/risk",
    response_model=RiskProfileResponse,
    summary="Get agent risk profile",
    description="Get the most recent risk profile for an agent"
)
async def get_risk_profile(
    agent_id: UUID,
    capability_profile_id: Optional[UUID] = None,
    service: RiskAnalysisService = Depends(get_service)
):
    """
    Get existing risk profile for an agent.
    
    If capability_profile_id provided, returns risk for that specific analysis.
    Otherwise returns most recent risk profile.
    """
    profile = service.get_profile(agent_id=agent_id, capability_profile_id=capability_profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk profile found for agent {agent_id}"
        )
    return service.to_response(profile)


@router.get(
    "/{agent_id}/risk/history",
    response_model=list[RiskProfileResponse],
    summary="Get agent risk history",
    description="Get all risk profiles for an agent"
)
async def get_risk_history(
    agent_id: UUID,
    limit: int = 10,
    service: RiskAnalysisService = Depends(get_service)
):
    """
    Get history of risk analyses for an agent.
    
    Useful for tracking how risk assessment evolved over time.
    """
    profiles = service.list_profiles(agent_id=agent_id, limit=limit)
    return [service.to_response(p) for p in profiles]
