"""
Agent Registry API routes.

REST API endpoints for agent management.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database.base import get_db
from modules.agent_registry.application.service import AgentService
from modules.agent_registry.domain.schemas import (
    CreateAgentRequest,
    UpdateAgentRequest,
    AgentResponse,
    AgentFilters,
    ExecutionMode,
)
from shared.types import PaginationParams, PaginatedResponse

router = APIRouter()


def get_agent_service(db: Session = Depends(get_db)) -> AgentService:
    """Dependency to get agent service instance."""
    return AgentService(db)


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="Register a new AI agent with configuration and metadata",
)
async def create_agent(
    request: CreateAgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """
    Create a new agent.
    
    - **name**: Unique agent name (1-255 characters)
    - **endpoint_url**: Agent execution endpoint URL
    - **execution_mode**: Execution mode (http, sdk, browser)
    - **description**: Optional agent description
    - **purpose**: Optional agent purpose/use case
    - **risk_profile**: Optional risk configuration
    - **metadata**: Optional additional metadata
    - **workspace_id**: Optional workspace identifier
    """
    return await service.create_agent(request)


@router.get(
    "",
    response_model=PaginatedResponse[AgentResponse],
    summary="List agents",
    description="Get a paginated list of agents with optional filtering",
)
def list_agents(
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    execution_mode: Optional[ExecutionMode] = Query(None, description="Filter by execution mode"),
    status: Optional[str] = Query(None, description="Filter by status"),
    workspace_id: Optional[UUID] = Query(None, description="Filter by workspace"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: AgentService = Depends(get_agent_service),
) -> PaginatedResponse[AgentResponse]:
    """
    List agents with optional filtering and pagination.
    
    Returns a paginated list of agents matching the specified filters.
    """
    filters = AgentFilters(
        name=name,
        execution_mode=execution_mode,
        status=status,
        workspace_id=workspace_id,
    )
    pagination = PaginationParams(page=page, page_size=page_size)
    
    return service.list_agents(filters, pagination)


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Get agent by ID",
    description="Retrieve detailed information about a specific agent",
)
def get_agent(
    agent_id: UUID,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """
    Get agent by ID.
    
    Returns detailed information about the specified agent.
    """
    return service.get_agent(agent_id)


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Update agent",
    description="Update agent configuration and metadata",
)
async def update_agent(
    agent_id: UUID,
    request: UpdateAgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """
    Update an agent.
    
    Only provided fields will be updated. All fields are optional.
    """
    return await service.update_agent(agent_id, request)


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive agent",
    description="Archive (soft delete) an agent",
)
async def archive_agent(
    agent_id: UUID,
    service: AgentService = Depends(get_agent_service),
) -> None:
    """
    Archive an agent.
    
    This is a soft delete - the agent is marked as archived but not removed from the database.
    Archived agents can still be queried but won't appear in default listings.
    """
    await service.archive_agent(agent_id)
