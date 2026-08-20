"""
Agent Version Repository implementation.

Handles database operations for agent versions.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from modules.agent_versioning.domain.models import AgentVersion
from shared.types import PaginationParams
from shared.exceptions import NotFoundError, DatabaseError


class AgentVersionRepository:
    """
    Repository for agent version database operations.
    
    Encapsulates all database access logic for agent versions.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, version: AgentVersion) -> AgentVersion:
        """
        Create a new agent version.
        
        Args:
            version: AgentVersion instance to create
            
        Returns:
            Created version with generated ID
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            self.db.add(version)
            self.db.flush()
            self.db.refresh(version)
            return version
        except Exception as e:
            raise DatabaseError(f"Failed to create agent version: {str(e)}")

    def get_by_id(self, version_id: UUID) -> Optional[AgentVersion]:
        """
        Get version by ID.
        
        Args:
            version_id: Version UUID
            
        Returns:
            AgentVersion if found, None otherwise
        """
        stmt = select(AgentVersion).where(AgentVersion.id == version_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_agent_and_version_number(
        self, agent_id: UUID, version_number: str
    ) -> Optional[AgentVersion]:
        """
        Get version by agent ID and version number.
        
        Args:
            agent_id: Agent UUID
            version_number: Version identifier
            
        Returns:
            AgentVersion if found, None otherwise
        """
        stmt = select(AgentVersion).where(
            AgentVersion.agent_id == agent_id,
            AgentVersion.version_number == version_number,
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_agent(
        self, agent_id: UUID, pagination: Optional[PaginationParams] = None
    ) -> tuple[List[AgentVersion], int]:
        """
        List versions for an agent.
        
        Args:
            agent_id: Agent UUID
            pagination: Optional pagination parameters
            
        Returns:
            Tuple of (versions list, total count)
        """
        # Base query
        stmt = select(AgentVersion).where(AgentVersion.agent_id == agent_id)
        count_stmt = (
            select(func.count())
            .select_from(AgentVersion)
            .where(AgentVersion.agent_id == agent_id)
        )

        # Get total count
        total = self.db.execute(count_stmt).scalar_one()

        # Apply ordering (newest first)
        stmt = stmt.order_by(desc(AgentVersion.created_at))

        # Apply pagination
        if pagination:
            stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

        # Execute query
        result = self.db.execute(stmt)
        versions = list(result.scalars().all())

        return versions, total

    def get_latest_version(self, agent_id: UUID) -> Optional[AgentVersion]:
        """
        Get the most recent version for an agent.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Latest AgentVersion if exists, None otherwise
        """
        stmt = (
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent_id)
            .order_by(desc(AgentVersion.created_at))
            .limit(1)
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_next_version_number(self, agent_id: UUID) -> str:
        """
        Generate next sequential version number for an agent.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Next version number (e.g., "v1", "v2", etc.)
        """
        # Count existing versions
        stmt = (
            select(func.count())
            .select_from(AgentVersion)
            .where(AgentVersion.agent_id == agent_id)
        )
        count = self.db.execute(stmt).scalar_one()
        
        # Return next sequential number
        return f"v{count + 1}"

    def version_number_exists(
        self, agent_id: UUID, version_number: str
    ) -> bool:
        """
        Check if version number exists for agent.
        
        Args:
            agent_id: Agent UUID
            version_number: Version identifier
            
        Returns:
            True if exists, False otherwise
        """
        stmt = (
            select(func.count())
            .select_from(AgentVersion)
            .where(
                AgentVersion.agent_id == agent_id,
                AgentVersion.version_number == version_number,
            )
        )
        count = self.db.execute(stmt).scalar_one()
        return count > 0

    def count_versions(self, agent_id: UUID) -> int:
        """
        Count total versions for an agent.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Total version count
        """
        stmt = (
            select(func.count())
            .select_from(AgentVersion)
            .where(AgentVersion.agent_id == agent_id)
        )
        return self.db.execute(stmt).scalar_one()
