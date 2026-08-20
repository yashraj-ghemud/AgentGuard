"""
Agent Service - Application layer.

Orchestrates business logic and coordinates between layers.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from modules.agent_registry.domain.models import Agent
from modules.agent_registry.domain.schemas import (
    CreateAgentRequest,
    UpdateAgentRequest,
    AgentResponse,
    AgentFilters,
)
from modules.agent_registry.infrastructure.repository import AgentRepository
from shared.types import PaginationParams, PaginatedResponse, EntityStatus
from shared.exceptions import NotFoundError, ConflictError
from shared.utils import generate_id, utc_now
from core.events.local_publisher import get_event_publisher
from core.events.domain_events import AgentCreated, AgentUpdated, AgentDeleted
from core.observability.logging import get_logger

logger = get_logger(__name__)


class AgentService:
    """
    Agent service for business logic.
    
    Handles agent lifecycle operations, validation, and event publishing.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = AgentRepository(db)
        self.event_publisher = get_event_publisher()

    async def create_agent(self, request: CreateAgentRequest) -> AgentResponse:
        """
        Create a new agent.
        
        Args:
            request: Agent creation request
            
        Returns:
            Created agent
            
        Raises:
            ConflictError: If agent with same name exists
        """
        # Check for duplicate name
        if self.repository.exists_by_name(request.name, request.workspace_id):
            raise ConflictError(
                f"Agent with name '{request.name}' already exists",
                details={"name": request.name},
            )

        # Create agent entity
        agent = Agent(
            id=generate_id(),
            name=request.name,
            description=request.description,
            endpoint_url=request.endpoint_url,
            execution_mode=request.execution_mode.value,
            purpose=request.purpose,
            status=EntityStatus.ACTIVE,
            risk_profile=request.risk_profile.model_dump() if request.risk_profile else {},
            agent_metadata=request.metadata,
            workspace_id=request.workspace_id,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        # Persist to database
        agent = self.repository.create(agent)
        self.db.commit()

        logger.info(
            f"Agent created: {agent.name}",
            extra={"agent_id": str(agent.id), "name": agent.name},
        )

        # Publish domain event
        await self.event_publisher.publish(
            AgentCreated(
                agent_id=agent.id,
                agent_name=agent.name,
                workspace_id=agent.workspace_id,
            )
        )

        return AgentResponse.model_validate(agent)

    def get_agent(self, agent_id: UUID) -> AgentResponse:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Agent data
            
        Raises:
            NotFoundError: If agent not found
        """
        agent = self.repository.get_by_id(agent_id)
        if not agent:
            raise NotFoundError("Agent", str(agent_id))

        return AgentResponse.model_validate(agent)

    def list_agents(
        self,
        filters: Optional[AgentFilters] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> PaginatedResponse[AgentResponse]:
        """
        List agents with filtering and pagination.
        
        Args:
            filters: Optional filters
            pagination: Optional pagination parameters
            
        Returns:
            Paginated list of agents
        """
        if pagination is None:
            pagination = PaginationParams()

        agents, total = self.repository.list(filters, pagination)

        agent_responses = [AgentResponse.model_validate(agent) for agent in agents]

        return PaginatedResponse.create(
            items=agent_responses,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def update_agent(
        self, agent_id: UUID, request: UpdateAgentRequest
    ) -> AgentResponse:
        """
        Update an agent.
        
        Args:
            agent_id: Agent UUID
            request: Update request with fields to change
            
        Returns:
            Updated agent
            
        Raises:
            NotFoundError: If agent not found
            ConflictError: If updated name conflicts with existing agent
        """
        # Get existing agent
        agent = self.repository.get_by_id(agent_id)
        if not agent:
            raise NotFoundError("Agent", str(agent_id))

        # Track changes for event
        changes = {}

        # Update fields
        if request.name is not None and request.name != agent.name:
            # Check for duplicate name
            if self.repository.exists_by_name(
                request.name, agent.workspace_id, exclude_id=agent_id
            ):
                raise ConflictError(
                    f"Agent with name '{request.name}' already exists",
                    details={"name": request.name},
                )
            changes["name"] = {"old": agent.name, "new": request.name}
            agent.name = request.name

        if request.description is not None and request.description != agent.description:
            changes["description"] = {"old": agent.description, "new": request.description}
            agent.description = request.description

        if request.endpoint_url is not None and request.endpoint_url != agent.endpoint_url:
            changes["endpoint_url"] = {"old": agent.endpoint_url, "new": request.endpoint_url}
            agent.endpoint_url = request.endpoint_url

        if request.purpose is not None and request.purpose != agent.purpose:
            changes["purpose"] = {"old": agent.purpose, "new": request.purpose}
            agent.purpose = request.purpose

        if request.risk_profile is not None:
            new_profile = request.risk_profile.model_dump()
            if new_profile != agent.risk_profile:
                changes["risk_profile"] = {"old": agent.risk_profile, "new": new_profile}
                agent.risk_profile = new_profile

        if request.metadata is not None and request.metadata != agent.agent_metadata:
            changes["metadata"] = {"old": agent.agent_metadata, "new": request.metadata}
            agent.agent_metadata = request.metadata

        # Update timestamp
        agent.updated_at = utc_now()

        # Persist changes
        agent = self.repository.update(agent)
        self.db.commit()

        if changes:
            logger.info(
                f"Agent updated: {agent.name}",
                extra={
                    "agent_id": str(agent.id),
                    "name": agent.name,
                    "changes": list(changes.keys()),
                },
            )

            # Publish domain event
            await self.event_publisher.publish(
                AgentUpdated(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    changes=changes,
                    workspace_id=agent.workspace_id,
                )
            )

        return AgentResponse.model_validate(agent)

    async def archive_agent(self, agent_id: UUID) -> None:
        """
        Archive (soft delete) an agent.
        
        Args:
            agent_id: Agent UUID
            
        Raises:
            NotFoundError: If agent not found
        """
        agent = self.repository.archive(agent_id)
        self.db.commit()

        logger.info(
            f"Agent archived: {agent.name}",
            extra={"agent_id": str(agent.id), "name": agent.name},
        )

        # Publish domain event
        await self.event_publisher.publish(
            AgentDeleted(
                agent_id=agent.id,
                agent_name=agent.name,
                workspace_id=agent.workspace_id,
            )
        )
