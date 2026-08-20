"""
Agent Version Service - Application layer.

Orchestrates version snapshot creation and retrieval.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from modules.agent_versioning.domain.models import AgentVersion
from modules.agent_versioning.domain.schemas import (
    CreateVersionRequest,
    AgentVersionResponse,
    AgentVersionSummary,
    AgentSnapshotData,
)
from modules.agent_versioning.infrastructure.repository import AgentVersionRepository
from modules.agent_registry.infrastructure.repository import AgentRepository
from shared.types import PaginationParams, PaginatedResponse
from shared.exceptions import NotFoundError, ConflictError
from shared.utils import generate_id, utc_now
from core.events.local_publisher import get_event_publisher
from core.events.domain_events import AgentVersionCreated
from core.observability.logging import get_logger

logger = get_logger(__name__)


class AgentVersionService:
    """
    Agent version service for snapshot management.
    
    Handles creating and retrieving immutable agent version snapshots.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = AgentVersionRepository(db)
        self.agent_repository = AgentRepository(db)
        self.event_publisher = get_event_publisher()

    async def create_version(
        self, agent_id: UUID, request: CreateVersionRequest
    ) -> AgentVersionResponse:
        """
        Create a new immutable version snapshot of an agent.
        
        Args:
            agent_id: Agent UUID to snapshot
            request: Version creation request
            
        Returns:
            Created version
            
        Raises:
            NotFoundError: If agent not found
            ConflictError: If version number already exists
        """
        # Get agent data
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise NotFoundError("Agent", str(agent_id))

        # Determine version number
        version_number = request.version_number
        if not version_number:
            # Auto-generate sequential version number
            version_number = self.repository.get_next_version_number(agent_id)
        else:
            # Check for duplicate version number
            if self.repository.version_number_exists(agent_id, version_number):
                raise ConflictError(
                    f"Version '{version_number}' already exists for this agent",
                    details={"agent_id": str(agent_id), "version_number": version_number},
                )

        # Create snapshot of agent configuration
        snapshot_data = AgentSnapshotData(
            agent_id=agent.id,
            name=agent.name,
            description=agent.description,
            endpoint_url=agent.endpoint_url,
            execution_mode=agent.execution_mode,
            purpose=agent.purpose,
            status=agent.status.value if hasattr(agent.status, "value") else agent.status,
            risk_profile=agent.risk_profile or {},
            metadata=agent.agent_metadata or {},
            workspace_id=agent.workspace_id,
            captured_at=utc_now(),
            tool_ids=[],  # Will be populated when Tool Registry integration is added
        )

        # Create version entity
        version = AgentVersion(
            id=generate_id(),
            agent_id=agent_id,
            version_number=version_number,
            snapshot=snapshot_data.model_dump(),
            notes=request.notes,
            snapshot_metadata=request.snapshot_metadata,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        # Persist to database
        version = self.repository.create(version)
        self.db.commit()

        logger.info(
            f"Agent version created: {agent.name} {version_number}",
            extra={
                "agent_id": str(agent_id),
                "version_id": str(version.id),
                "version_number": version_number,
            },
        )

        # Publish domain event
        await self.event_publisher.publish(
            AgentVersionCreated(
                agent_id=agent_id,
                version_id=version.id,
                version_number=version_number,
                workspace_id=agent.workspace_id,
            )
        )

        return AgentVersionResponse.from_db_model(version)

    def get_version(self, agent_id: UUID, version_id: UUID) -> AgentVersionResponse:
        """
        Get a specific version by ID.
        
        Args:
            agent_id: Agent UUID
            version_id: Version UUID
            
        Returns:
            Version data
            
        Raises:
            NotFoundError: If version not found or doesn't belong to agent
        """
        version = self.repository.get_by_id(version_id)
        if not version or version.agent_id != agent_id:
            raise NotFoundError("AgentVersion", str(version_id))

        return AgentVersionResponse.from_db_model(version)

    def get_version_by_number(
        self, agent_id: UUID, version_number: str
    ) -> AgentVersionResponse:
        """
        Get a version by agent ID and version number.
        
        Args:
            agent_id: Agent UUID
            version_number: Version identifier
            
        Returns:
            Version data
            
        Raises:
            NotFoundError: If version not found
        """
        version = self.repository.get_by_agent_and_version_number(
            agent_id, version_number
        )
        if not version:
            raise NotFoundError(
                "AgentVersion",
                f"agent_id={agent_id}, version_number={version_number}",
            )

        return AgentVersionResponse.from_db_model(version)

    def list_versions(
        self, agent_id: UUID, pagination: Optional[PaginationParams] = None
    ) -> PaginatedResponse[AgentVersionSummary]:
        """
        List versions for an agent.
        
        Args:
            agent_id: Agent UUID
            pagination: Optional pagination parameters
            
        Returns:
            Paginated list of version summaries
        """
        # Verify agent exists
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise NotFoundError("Agent", str(agent_id))

        if pagination is None:
            pagination = PaginationParams()

        versions, total = self.repository.list_by_agent(agent_id, pagination)

        version_summaries = [
            AgentVersionSummary(
                id=v.id,
                agent_id=v.agent_id,
                version_number=v.version_number,
                notes=v.notes,
                created_at=v.created_at,
            )
            for v in versions
        ]

        return PaginatedResponse.create(
            items=version_summaries,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def get_latest_version(self, agent_id: UUID) -> Optional[AgentVersionResponse]:
        """
        Get the most recent version for an agent.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Latest version if exists, None otherwise
        """
        # Verify agent exists
        agent = self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise NotFoundError("Agent", str(agent_id))

        version = self.repository.get_latest_version(agent_id)
        if not version:
            return None

        return AgentVersionResponse.from_db_model(version)
