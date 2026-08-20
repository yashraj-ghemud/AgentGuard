"""
Tool Registry API routes.

REST API endpoints for tool management.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database.base import get_db
from modules.tool_registry.application.service import ToolService
from modules.tool_registry.domain.schemas import (
    RegisterToolRequest,
    UpdateToolRequest,
    ToolResponse,
    ToolFilters,
)
from shared.types import PaginationParams, PaginatedResponse, RiskLevel

router = APIRouter()


def get_tool_service(db: Session = Depends(get_db)) -> ToolService:
    """Dependency to get tool service instance."""
    return ToolService(db)


@router.post(
    "",
    response_model=ToolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a tool",
    description="Register a new tool for an agent with schema and risk profile",
)
async def register_tool(
    agent_id: UUID,
    request: RegisterToolRequest,
    service: ToolService = Depends(get_tool_service),
) -> ToolResponse:
    """
    Register a new tool for an agent.
    
    Tools define actions the agent can perform with:
    - **name**: Unique tool name (per agent)
    - **description**: What the tool does
    - **input_schema**: JSON Schema for tool inputs
    - **output_schema**: Optional JSON Schema for outputs
    - **risk_level**: low, medium, high, critical
    - **is_destructive**: Whether tool modifies state
    - **is_reversible**: Whether action can be undone
    - **requires_confirmation**: Whether user approval is needed
    - **timeout_seconds**: Max execution time
    """
    return await service.register_tool(agent_id, request)


@router.get(
    "",
    response_model=PaginatedResponse[ToolResponse],
    summary="List agent tools",
    description="Get paginated list of tools for an agent with optional filtering",
)
def list_agent_tools(
    agent_id: UUID,
    risk_level: Optional[RiskLevel] = Query(None, description="Filter by risk level"),
    is_destructive: Optional[bool] = Query(None, description="Filter by destructive flag"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ToolService = Depends(get_tool_service),
) -> PaginatedResponse[ToolResponse]:
    """
    List all tools for an agent.
    
    Returns tools with optional filtering by risk level, destructiveness, or status.
    """
    filters = ToolFilters(
        risk_level=risk_level,
        is_destructive=is_destructive,
        status=status,
    )
    pagination = PaginationParams(page=page, page_size=page_size)
    
    return service.list_agent_tools(agent_id, filters, pagination)


# Note: We also provide a global tool endpoint for direct access
@router.get(
    "/{tool_id}",
    response_model=ToolResponse,
    summary="Get tool by ID",
    description="Retrieve detailed information about a specific tool",
    tags=["Tools"],
)
def get_tool(
    tool_id: UUID,
    service: ToolService = Depends(get_tool_service),
) -> ToolResponse:
    """
    Get a specific tool by ID.
    
    Returns complete tool definition including schemas and risk profile.
    """
    return service.get_tool(tool_id)


@router.patch(
    "/{tool_id}",
    response_model=ToolResponse,
    summary="Update tool",
    description="Update tool configuration and schemas",
    tags=["Tools"],
)
async def update_tool(
    tool_id: UUID,
    request: UpdateToolRequest,
    service: ToolService = Depends(get_tool_service),
) -> ToolResponse:
    """
    Update a tool.
    
    Only provided fields will be updated. All fields are optional.
    Note: Tool name cannot be changed (create new tool instead).
    """
    return await service.update_tool(tool_id, request)


@router.delete(
    "/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive tool",
    description="Archive (soft delete) a tool",
    tags=["Tools"],
)
async def archive_tool(
    tool_id: UUID,
    service: ToolService = Depends(get_tool_service),
) -> None:
    """
    Archive a tool.
    
    This is a soft delete - the tool is marked as archived but not removed.
    Archived tools won't appear in default listings but remain in the database
    for historical reference.
    """
    await service.archive_tool(tool_id)
