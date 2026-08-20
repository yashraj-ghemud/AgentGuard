"""
Risk Analysis Repository

Data access layer for risk profiles.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from modules.risk_analysis.domain.models import RiskProfile


class RiskAnalysisRepository:
    """Repository for risk profiles."""

    def __init__(self, db: Session):
        """
        Initialize repository.
        
        Args:
            db: Database session
        """
        self.db = db

    def create(self, profile: RiskProfile) -> RiskProfile:
        """
        Create a new risk profile.
        
        Args:
            profile: Risk profile to create
            
        Returns:
            Created profile
        """
        self.db.add(profile)
        self.db.flush()
        self.db.refresh(profile)
        return profile

    def get_by_id(self, profile_id: UUID) -> Optional[RiskProfile]:
        """
        Get profile by ID.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Profile if found, None otherwise
        """
        return self.db.query(RiskProfile).filter(
            RiskProfile.id == profile_id
        ).first()

    def get_by_agent(
        self,
        agent_id: UUID,
        capability_profile_id: Optional[UUID] = None
    ) -> Optional[RiskProfile]:
        """
        Get risk profile for an agent.
        
        Args:
            agent_id: Agent ID
            capability_profile_id: Optional capability profile ID
            
        Returns:
            Most recent profile matching criteria
        """
        query = self.db.query(RiskProfile).filter(
            RiskProfile.agent_id == agent_id
        )
        
        if capability_profile_id:
            query = query.filter(RiskProfile.capability_profile_id == capability_profile_id)
        
        # Get most recent
        return query.order_by(desc(RiskProfile.created_at)).first()

    def list_by_agent(
        self,
        agent_id: UUID,
        limit: int = 10
    ) -> List[RiskProfile]:
        """
        List all risk profiles for an agent.
        
        Args:
            agent_id: Agent ID
            limit: Maximum results
            
        Returns:
            List of profiles
        """
        return self.db.query(RiskProfile).filter(
            RiskProfile.agent_id == agent_id
        ).order_by(
            desc(RiskProfile.created_at)
        ).limit(limit).all()

    def delete(self, profile_id: UUID) -> bool:
        """
        Delete a risk profile.
        
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

    def update(self, profile: RiskProfile) -> RiskProfile:
        """
        Update a risk profile.
        
        Args:
            profile: Profile with updated data
            
        Returns:
            Updated profile
        """
        self.db.flush()
        self.db.refresh(profile)
        return profile
