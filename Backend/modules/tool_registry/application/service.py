"""
Tool Service - Application layer.

Orchestrates tool registration and management.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from modules.tool_registry.domain.models import Tool
from modules.tool_registry.domain.schemas import (
    RegisterToolRequest,
    UpdateToolRequest,
    ToolResponse,
    ToolFilters,
)
from modules.tool_registry.infrastructure.repository import ToolRepository
from modules.agent_registry.infrastructure.repository import AgentRepository
from shared.types import PaginationParams, PaginatedResponse, EntityStatus
from shared.exceptions import NotFoundError, ConflictError
from shared.utils import generate_id, utc_now
from core.events.local_publisher import get_event_publisher
from core.events.domain_events import ToolRegistered, ToolUpdated, ToolDeleted
from core.observability.logging import get_logger

logger = get_logger(__name__)


class ToolService:
    """
    Tool service for tool management.
    
    Handles tool registration, updates, and retrieval with validation.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = ToolRepository(db)
        self.agent_repository = AgentRepository(db)
        self.event_publisher = get_event_publisher()

    async def register_tool(
        self, agent_id: UUID, request: RegisterToolRequest
    ) -> ToolResponse:
        """
        Register a new tool for an agent.
        
        Args:
            agent_id: Agent UUID
            request: Tool registration request
            
        Returns:
            Registered tool
            
        Raises:
            NotFoundError: If agent not found
            ConflictError: If tool name already exists for agent
        """
        # Verify agent exists
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise NotFoundError("Agent", str(agent_id))

        # Check for duplicate name
        if self.repository.exists_by_name(agent_id, request.name):
            raise ConflictError(
                f"Tool with name '{request.name}' already exists for this agent",
                details={"agent_id": str(agent_id), "tool_name": request.name},
            )

        # Create tool entity
        tool = Tool(
            id=generate_id(),
            agent_id=agent_id,
            name=request.name,
            description=request.description,
            input_schema=request.input_schema,
            output_schema=request.output_schema,
            risk_level=request.risk_level.value,
            is_destructive=request.is_destructive,
            is_reversible=request.is_reversible,
            requires_confirmation=request.requires_confirmation,
            timeout_seconds=request.timeout_seconds,
            status=EntityStatus.ACTIVE.value,
            tool_metadata=request.metadata,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        # Persist to database
        tool = self.repository.create(tool)
        self.db.commit()

        logger.info(
            f"Tool registered: {tool.name} for agent {agent.name}",
            extra={
                "tool_id": str(tool.id),
                "tool_name": tool.name,
                "agent_id": str(agent_id),
                "risk_level": tool.risk_level,
            },
        )

        # Publish domain event
        await self.event_publisher.publish(
            ToolRegistered(
                tool_id=tool.id,
                tool_name=tool.name,
                agent_id=agent_id,
                risk_level=tool.risk_level,
                workspace_id=agent.workspace_id,
            )
        )

        return ToolResponse.model_validate(tool)

    def get_tool(self, tool_id: UUID) -> ToolResponse:
        """
        Get tool by ID.
        
        Args:
            tool_id: Tool UUID
            
        Returns:
            Tool data
            
        Raises:
            NotFoundError: If tool not found
        """
        tool = self.repository.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", str(tool_id))

        return ToolResponse.model_validate(tool)

    def list_agent_tools(
        self,
        agent_id: UUID,
        filters: Optional[ToolFilters] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> PaginatedResponse[ToolResponse]:
        """
        List tools for an agent with filtering and pagination.
        
        Args:
            agent_id: Agent UUID
            filters: Optional filters
            pagination: Optional pagination parameters
            
        Returns:
            Paginated list of tools
        """
        # Verify agent exists
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise NotFoundError("Agent", str(agent_id))

        if pagination is None:
            pagination = PaginationParams()

        tools, total = self.repository.list_by_agent(agent_id, filters, pagination)

        tool_responses = [ToolResponse.model_validate(tool) for tool in tools]

        return PaginatedResponse.create(
            items=tool_responses,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def update_tool(
        self, tool_id: UUID, request: UpdateToolRequest
    ) -> ToolResponse:
        """
        Update a tool.
        
        Args:
            tool_id: Tool UUID
            request: Update request with fields to change
            
        Returns:
            Updated tool
            
        Raises:
            NotFoundError: If tool not found
        """
        # Get existing tool
        tool = self.repository.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", str(tool_id))

        # Track changes for event
        changes = {}

        # Update fields
        if request.description is not None and request.description != tool.description:
            changes["description"] = {"old": tool.description, "new": request.description}
            tool.description = request.description

        if request.input_schema is not None and request.input_schema != tool.input_schema:
            changes["input_schema"] = {"old": tool.input_schema, "new": request.input_schema}
            tool.input_schema = request.input_schema

        if request.output_schema is not None and request.output_schema != tool.output_schema:
            changes["output_schema"] = {"old": tool.output_schema, "new": request.output_schema}
            tool.output_schema = request.output_schema

        if request.risk_level is not None and request.risk_level.value != tool.risk_level:
            changes["risk_level"] = {"old": tool.risk_level, "new": request.risk_level.value}
            tool.risk_level = request.risk_level.value

        if request.is_destructive is not None and request.is_destructive != tool.is_destructive:
            changes["is_destructive"] = {"old": tool.is_destructive, "new": request.is_destructive}
            tool.is_destructive = request.is_destructive

        if request.is_reversible is not None and request.is_reversible != tool.is_reversible:
            changes["is_reversible"] = {"old": tool.is_reversible, "new": request.is_reversible}
            tool.is_reversible = request.is_reversible

        if (
            request.requires_confirmation is not None
            and request.requires_confirmation != tool.requires_confirmation
        ):
            changes["requires_confirmation"] = {
                "old": tool.requires_confirmation,
                "new": request.requires_confirmation,
            }
            tool.requires_confirmation = request.requires_confirmation

        if (
            request.timeout_seconds is not None
            and request.timeout_seconds != tool.timeout_seconds
        ):
            changes["timeout_seconds"] = {
                "old": tool.timeout_seconds,
                "new": request.timeout_seconds,
            }
            tool.timeout_seconds = request.timeout_seconds

        if request.metadata is not None and request.metadata != tool.tool_metadata:
            changes["metadata"] = {"old": tool.tool_metadata, "new": request.metadata}
            tool.tool_metadata = request.metadata

        # Update timestamp
        tool.updated_at = utc_now()

        # Persist changes
        tool = self.repository.update(tool)
        self.db.commit()

        if changes:
            logger.info(
                f"Tool updated: {tool.name}",
                extra={
                    "tool_id": str(tool.id),
                    "tool_name": tool.name,
                    "changes": list(changes.keys()),
                },
            )

            # Publish domain event
            await self.event_publisher.publish(
                ToolUpdated(
                    tool_id=tool.id,
                    tool_name=tool.name,
                    agent_id=tool.agent_id,
                    changes=changes,
                )
            )

        return ToolResponse.model_validate(tool)

    async def archive_tool(self, tool_id: UUID) -> None:
        """
        Archive (soft delete) a tool.
        
        Args:
            tool_id: Tool UUID
            
        Raises:
            NotFoundError: If tool not found
        """
        tool = self.repository.archive(tool_id)
        self.db.commit()

        logger.info(
            f"Tool archived: {tool.name}",
            extra={"tool_id": str(tool.id), "tool_name": tool.name},
        )

        # Publish domain event
        await self.event_publisher.publish(
            ToolDeleted(
                tool_id=tool.id,
                tool_name=tool.name,
                agent_id=tool.agent_id,
            )
        )
