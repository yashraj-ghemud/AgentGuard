"""
Agent Repository implementation.

Handles database operations for agents.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from modules.agent_registry.domain.models import Agent
from modules.agent_registry.domain.schemas import AgentFilters
from shared.types import EntityStatus, PaginationParams
from shared.exceptions import NotFoundError, DatabaseError


class AgentRepository:
    """
    Repository for agent database operations.
    
    Encapsulates all database access logic for agents.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, agent: Agent) -> Agent:
        """
        Create a new agent.
        
        Args:
            agent: Agent instance to create
            
        Returns:
            Created agent with generated ID
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            self.db.add(agent)
            self.db.flush()
            self.db.refresh(agent)
            return agent
        except Exception as e:
            raise DatabaseError(f"Failed to create agent: {str(e)}")

    def get_by_id(self, agent_id: UUID) -> Optional[Agent]:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Agent if found, None otherwise
        """
        stmt = select(Agent).where(Agent.id == agent_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_name(
        self, name: str, workspace_id: Optional[UUID] = None
    ) -> Optional[Agent]:
        """
        Get agent by name.
        
        Args:
            name: Agent name
            workspace_id: Optional workspace ID for scoping
            
        Returns:
            Agent if found, None otherwise
        """
        stmt = select(Agent).where(Agent.name == name)
        if workspace_id is not None:
            stmt = stmt.where(Agent.workspace_id == workspace_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def list(
        self,
        filters: Optional[AgentFilters] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> tuple[List[Agent], int]:
        """
        List agents with optional filtering and pagination.
        
        Args:
            filters: Optional filters to apply
            pagination: Optional pagination parameters
            
        Returns:
            Tuple of (agents list, total count)
        """
        # Base query
        stmt = select(Agent)
        count_stmt = select(func.count()).select_from(Agent)

        # Apply filters
        if filters:
            conditions = []
            
            if filters.name:
                # Partial name match (case-insensitive)
                conditions.append(Agent.name.ilike(f"%{filters.name}%"))
            
            if filters.execution_mode:
                conditions.append(Agent.execution_mode == filters.execution_mode.value)
            
            if filters.status:
                conditions.append(Agent.status == filters.status)
            
            if filters.workspace_id:
                conditions.append(Agent.workspace_id == filters.workspace_id)
            
            if conditions:
                stmt = stmt.where(*conditions)
                count_stmt = count_stmt.where(*conditions)

        # Get total count
        total = self.db.execute(count_stmt).scalar_one()

        # Apply ordering
        stmt = stmt.order_by(Agent.created_at.desc())

        # Apply pagination
        if pagination:
            stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

        # Execute query
        result = self.db.execute(stmt)
        agents = list(result.scalars().all())

        return agents, total

    def update(self, agent: Agent) -> Agent:
        """
        Update an agent.
        
        Args:
            agent: Agent instance with updated fields
            
        Returns:
            Updated agent
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            self.db.flush()
            self.db.refresh(agent)
            return agent
        except Exception as e:
            raise DatabaseError(f"Failed to update agent: {str(e)}")

    def delete(self, agent_id: UUID) -> None:
        """
        Hard delete an agent.
        
        Note: Prefer soft delete (archive) in most cases.
        
        Args:
            agent_id: Agent UUID
            
        Raises:
            NotFoundError: If agent not found
            DatabaseError: If deletion fails
        """
        agent = self.get_by_id(agent_id)
        if not agent:
            raise NotFoundError("Agent", str(agent_id))
        
        try:
            self.db.delete(agent)
            self.db.flush()
        except Exception as e:
            raise DatabaseError(f"Failed to delete agent: {str(e)}")

    def archive(self, agent_id: UUID) -> Agent:
        """
        Soft delete an agent by marking as archived.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            Archived agent
            
        Raises:
            NotFoundError: If agent not found
        """
        agent = self.get_by_id(agent_id)
        if not agent:
            raise NotFoundError("Agent", str(agent_id))
        
        agent.status = EntityStatus.ARCHIVED
        return self.update(agent)

    def exists_by_name(
        self, name: str, workspace_id: Optional[UUID] = None, exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if agent with given name exists.
        
        Args:
            name: Agent name
            workspace_id: Optional workspace ID for scoping
            exclude_id: Optional agent ID to exclude (for update checks)
            
        Returns:
            True if exists, False otherwise
        """
        stmt = select(func.count()).select_from(Agent).where(Agent.name == name)
        
        if workspace_id is not None:
            stmt = stmt.where(Agent.workspace_id == workspace_id)
        
        if exclude_id is not None:
            stmt = stmt.where(Agent.id != exclude_id)
        
        count = self.db.execute(stmt).scalar_one()
        return count > 0
