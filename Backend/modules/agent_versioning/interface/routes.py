"""
Agent Versioning API routes.

REST API endpoints for agent version management.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database.base import get_db
from modules.agent_versioning.application.service import AgentVersionService
from modules.agent_versioning.domain.schemas import (
    CreateVersionRequest,
    AgentVersionResponse,
    AgentVersionSummary,
)
from shared.types import PaginationParams, PaginatedResponse

router = APIRouter()


def get_version_service(db: Session = Depends(get_db)) -> AgentVersionService:
    """Dependency to get agent version service instance."""
    return AgentVersionService(db)


@router.post(
    "",
    response_model=AgentVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent version snapshot",
    description="Create an immutable snapshot of agent configuration",
)
async def create_version(
    agent_id: UUID,
    request: CreateVersionRequest,
    service: AgentVersionService = Depends(get_version_service),
) -> AgentVersionResponse:
    """
    Create a new version snapshot for an agent.
    
    The snapshot captures the complete agent configuration at this point in time.
    Versions are immutable and cannot be modified after creation.
    
    - **version_number**: Optional version identifier (auto-generated if not provided)
    - **notes**: Optional version notes or changelog
    - **snapshot_metadata**: Optional additional metadata
    """
    return await service.create_version(agent_id, request)


@router.get(
    "",
    response_model=PaginatedResponse[AgentVersionSummary],
    summary="List agent versions",
    description="Get paginated list of versions for an agent",
)
def list_versions(
    agent_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: AgentVersionService = Depends(get_version_service),
) -> PaginatedResponse[AgentVersionSummary]:
    """
    List all versions for an agent.
    
    Returns versions in reverse chronological order (newest first).
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    return service.list_versions(agent_id, pagination)


@router.get(
    "/latest",
    response_model=AgentVersionResponse,
    summary="Get latest version",
    description="Get the most recent version snapshot for an agent",
)
def get_latest_version(
    agent_id: UUID,
    service: AgentVersionService = Depends(get_version_service),
) -> AgentVersionResponse:
    """
    Get the latest version for an agent.
    
    Returns the most recently created version snapshot.
    """
    version = service.get_latest_version(agent_id)
    if not version:
        from shared.exceptions import NotFoundError
        raise NotFoundError("AgentVersion", f"No versions found for agent {agent_id}")
    return version


@router.get(
    "/{version_id}",
    response_model=AgentVersionResponse,
    summary="Get version by ID",
    description="Retrieve detailed information about a specific version",
)
def get_version(
    agent_id: UUID,
    version_id: UUID,
    service: AgentVersionService = Depends(get_version_service),
) -> AgentVersionResponse:
    """
    Get a specific version by ID.
    
    Returns the complete version snapshot including all agent configuration.
    """
    return service.get_version(agent_id, version_id)


@router.get(
    "/by-number/{version_number}",
    response_model=AgentVersionResponse,
    summary="Get version by version number",
    description="Retrieve version by its version number identifier",
)
def get_version_by_number(
    agent_id: UUID,
    version_number: str,
    service: AgentVersionService = Depends(get_version_service),
) -> AgentVersionResponse:
    """
    Get a version by its version number.
    
    This allows lookup by human-readable version identifiers like "v1", "1.0.0", etc.
    """
    return service.get_version_by_number(agent_id, version_number)
