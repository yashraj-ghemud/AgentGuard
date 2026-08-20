"""
Tool Repository implementation.

Handles database operations for tools.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from modules.tool_registry.domain.models import Tool
from modules.tool_registry.domain.schemas import ToolFilters
from shared.types import PaginationParams, EntityStatus
from shared.exceptions import NotFoundError, DatabaseError


class ToolRepository:
    """
    Repository for tool database operations.
    
    Encapsulates all database access logic for tools.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, tool: Tool) -> Tool:
        """
        Create a new tool.
        
        Args:
            tool: Tool instance to create
            
        Returns:
            Created tool with generated ID
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            self.db.add(tool)
            self.db.flush()
            self.db.refresh(tool)
            return tool
        except Exception as e:
            raise DatabaseError(f"Failed to create tool: {str(e)}")

    def get_by_id(self, tool_id: UUID) -> Optional[Tool]:
        """
        Get tool by ID.
        
        Args:
            tool_id: Tool UUID
            
        Returns:
            Tool if found, None otherwise
        """
        stmt = select(Tool).where(Tool.id == tool_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_agent_and_name(
        self, agent_id: UUID, name: str
    ) -> Optional[Tool]:
        """
        Get tool by agent ID and name.
        
        Args:
            agent_id: Agent UUID
            name: Tool name
            
        Returns:
            Tool if found, None otherwise
        """
        stmt = select(Tool).where(
            Tool.agent_id == agent_id,
            Tool.name == name,
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_agent(
        self,
        agent_id: UUID,
        filters: Optional[ToolFilters] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> tuple[List[Tool], int]:
        """
        List tools for an agent with optional filtering.
        
        Args:
            agent_id: Agent UUID
            filters: Optional filters to apply
            pagination: Optional pagination parameters
            
        Returns:
            Tuple of (tools list, total count)
        """
        # Base query
        stmt = select(Tool).where(Tool.agent_id == agent_id)
        count_stmt = (
            select(func.count())
            .select_from(Tool)
            .where(Tool.agent_id == agent_id)
        )

        # Apply filters
        if filters:
            conditions = []
            
            if filters.risk_level:
                conditions.append(Tool.risk_level == filters.risk_level.value)
            
            if filters.is_destructive is not None:
                conditions.append(Tool.is_destructive == filters.is_destructive)
            
            if filters.status:
                conditions.append(Tool.status == filters.status)
            
            if conditions:
                stmt = stmt.where(*conditions)
                count_stmt = count_stmt.where(*conditions)

        # Get total count
        total = self.db.execute(count_stmt).scalar_one()

        # Apply ordering
        stmt = stmt.order_by(Tool.name)

        # Apply pagination
        if pagination:
            stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

        # Execute query
        result = self.db.execute(stmt)
        tools = list(result.scalars().all())

        return tools, total

    def update(self, tool: Tool) -> Tool:
        """
        Update a tool.
        
        Args:
            tool: Tool instance with updated fields
            
        Returns:
            Updated tool
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            self.db.flush()
            self.db.refresh(tool)
            return tool
        except Exception as e:
            raise DatabaseError(f"Failed to update tool: {str(e)}")

    def delete(self, tool_id: UUID) -> None:
        """
        Hard delete a tool.
        
        Note: Prefer soft delete (archive) in most cases.
        
        Args:
            tool_id: Tool UUID
            
        Raises:
            NotFoundError: If tool not found
            DatabaseError: If deletion fails
        """
        tool = self.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", str(tool_id))
        
        try:
            self.db.delete(tool)
            self.db.flush()
        except Exception as e:
            raise DatabaseError(f"Failed to delete tool: {str(e)}")

    def archive(self, tool_id: UUID) -> Tool:
        """
        Soft delete a tool by marking as archived.
        
        Args:
            tool_id: Tool UUID
            
        Returns:
            Archived tool
            
        Raises:
            NotFoundError: If tool not found
        """
        tool = self.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", str(tool_id))
        
        tool.status = EntityStatus.ARCHIVED.value
        return self.update(tool)

    def exists_by_name(
        self, agent_id: UUID, name: str, exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if tool with given name exists for agent.
        
        Args:
            agent_id: Agent UUID
            name: Tool name
            exclude_id: Optional tool ID to exclude (for update checks)
            
        Returns:
            True if exists, False otherwise
        """
        stmt = (
            select(func.count())
            .select_from(Tool)
            .where(Tool.agent_id == agent_id, Tool.name == name)
        )
        
        if exclude_id is not None:
            stmt = stmt.where(Tool.id != exclude_id)
        
        count = self.db.execute(stmt).scalar_one()
        return count > 0

    def get_tool_ids_for_agent(self, agent_id: UUID) -> List[UUID]:
        """
        Get all tool IDs for an agent.
        
        Useful for snapshot creation in Agent Versioning.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            List of tool UUIDs
        """
        stmt = (
            select(Tool.id)
            .where(Tool.agent_id == agent_id)
            .where(Tool.status == EntityStatus.ACTIVE.value)
        )
        result = self.db.execute(stmt)
        return [row[0] for row in result.all()]
