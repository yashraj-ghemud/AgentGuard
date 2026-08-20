"""
Agent Intelligence Repository

Data access layer for agent capability profiles.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from modules.agent_intelligence.domain.models import AgentCapabilityProfile
from shared.exceptions import NotFoundError


class AgentIntelligenceRepository:
    """Repository for agent capability profiles."""

    def __init__(self, db: Session):
        """
        Initialize repository.
        
        Args:
            db: Database session
        """
        self.db = db

    def create(self, profile: AgentCapabilityProfile) -> AgentCapabilityProfile:
        """
        Create a new capability profile.
        
        Args:
            profile: Capability profile to create
            
        Returns:
            Created profile
        """
        self.db.add(profile)
        self.db.flush()
        self.db.refresh(profile)
        return profile

    def get_by_id(self, profile_id: UUID) -> Optional[AgentCapabilityProfile]:
        """
        Get profile by ID.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Profile if found, None otherwise
        """
        return self.db.query(AgentCapabilityProfile).filter(
            AgentCapabilityProfile.id == profile_id
        ).first()

    def get_by_agent(
        self,
        agent_id: UUID,
        version_id: Optional[UUID] = None
    ) -> Optional[AgentCapabilityProfile]:
        """
        Get profile for an agent, optionally for specific version.
        
        Args:
            agent_id: Agent ID
            version_id: Optional version ID
            
        Returns:
            Most recent profile matching criteria
        """
        query = self.db.query(AgentCapabilityProfile).filter(
            AgentCapabilityProfile.agent_id == agent_id
        )
        
        if version_id:
            query = query.filter(AgentCapabilityProfile.version_id == version_id)
        
        # Get most recent
        return query.order_by(desc(AgentCapabilityProfile.created_at)).first()

    def list_by_agent(
        self,
        agent_id: UUID,
        limit: int = 10
    ) -> List[AgentCapabilityProfile]:
        """
        List all profiles for an agent.
        
        Args:
            agent_id: Agent ID
            limit: Maximum results
            
        Returns:
            List of profiles
        """
        return self.db.query(AgentCapabilityProfile).filter(
            AgentCapabilityProfile.agent_id == agent_id
        ).order_by(
            desc(AgentCapabilityProfile.created_at)
        ).limit(limit).all()

    def delete(self, profile_id: UUID) -> bool:
        """
        Delete a capability profile.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            True if deleted, False if not found
        """
        profile = self.get_by_id(profile_id)
        if not profile:
            return False
        
        self.db.delete(profile)
        self.db.flush()
        return True

    def update(self, profile: AgentCapabilityProfile) -> AgentCapabilityProfile:
        """
        Update a capability profile.
        
        Args:
            profile: Profile with updated data
            
        Returns:
            Updated profile
        """
        self.db.flush()
        self.db.refresh(profile)
        return profile
