"""
Agent Intelligence API Routes

REST API endpoints for agent capability analysis.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database.base import get_db
from core.events.local_publisher import LocalEventPublisher
from modules.agent_intelligence.application.service import AgentIntelligenceService
from modules.agent_intelligence.domain.schemas import (
    AnalyzeAgentRequest,
    AgentCapabilityProfileResponse,
)
from shared.exceptions import NotFoundError, InternalError

router = APIRouter(prefix="/api/v1/agents", tags=["agent-intelligence"])


def get_service(db: Session = Depends(get_db)) -> AgentIntelligenceService:
    """Dependency to get intelligence service."""
    publisher = LocalEventPublisher()
    return AgentIntelligenceService(db=db, event_publisher=publisher)


@router.post(
    "/{agent_id}/intelligence/analyze",
    response_model=AgentCapabilityProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze agent capabilities",
    description="Analyze an agent to generate a structured capability profile using LLM"
)
async def analyze_agent(
    agent_id: UUID,
    version_id: Optional[UUID] = None,
    force_regenerate: bool = False,
    service: AgentIntelligenceService = Depends(get_service)
):
    """
    Analyze an agent's capabilities, risks, and potential failure points.
    
    This endpoint uses LLM to deeply understand:
    - Agent's goals and capabilities
    - Tool capabilities and risks
    - Potential failure surfaces
    - Security vulnerabilities
    - Ambiguity points
    
    Results are cached unless force_regenerate=true.
    """
    try:
        profile = await service.analyze_agent(
            agent_id=agent_id,
            version_id=version_id,
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
    "/{agent_id}/intelligence",
    response_model=AgentCapabilityProfileResponse,
    summary="Get agent capability profile",
    description="Get the most recent capability profile for an agent"
)
async def get_agent_intelligence(
    agent_id: UUID,
    version_id: Optional[UUID] = None,
    service: AgentIntelligenceService = Depends(get_service)
):
    """
    Get existing capability profile for an agent.
    
    If version_id provided, returns profile for that specific version.
    Otherwise returns most recent profile.
    """
    profile = service.get_profile(agent_id=agent_id, version_id=version_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No capability profile found for agent {agent_id}"
        )
    return service.to_response(profile)


@router.get(
    "/{agent_id}/intelligence/history",
    response_model=list[AgentCapabilityProfileResponse],
    summary="Get agent intelligence history",
    description="Get all capability profiles for an agent"
)
async def get_agent_intelligence_history(
    agent_id: UUID,
    limit: int = 10,
    service: AgentIntelligenceService = Depends(get_service)
):
    """
    Get history of capability analyses for an agent.
    
    Useful for tracking how agent understanding evolved over time.
    """
    profiles = service.list_profiles(agent_id=agent_id, limit=limit)
    return [service.to_response(p) for p in profiles]
