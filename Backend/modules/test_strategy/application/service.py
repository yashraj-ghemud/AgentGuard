"""
Test Strategy Service

Business logic for creating test strategies based on agent intelligence and risk.
"""
from typing import Optional, Dict
from uuid import UUID

from sqlalchemy.orm import Session

from modules.test_strategy.domain.models import TestStrategy
from modules.agent_intelligence.infrastructure.repository import AgentIntelligenceRepository
from modules.risk_analysis.infrastructure.repository import RiskAnalysisRepository
from core.llm import get_llm_provider, get_llm_settings
from shared.exceptions import NotFoundError, InternalError
from shared.scenario_types import ScenarioCategory, TestIntensity

GENERATOR_VERSION = "1.0.0"


class TestStrategyService:
    """Service for creating test strategies."""

    def __init__(self, db: Session):
        self.db = db
        self.intelligence_repo = AgentIntelligenceRepository(db)
        self.risk_repo = RiskAnalysisRepository(db)
        self.llm = get_llm_provider()
        self.settings = get_llm_settings()

    async def create_strategy(
        self,
        agent_id: UUID,
        capability_profile_id: Optional[UUID] = None,
        risk_profile_id: Optional[UUID] = None,
        custom_distribution: Optional[Dict[str, int]] = None
    ) -> TestStrategy:
        """Create test strategy based on intelligence and risk."""
        
        # Get profiles
        capability_profile = (
            self.intelligence_repo.get_by_id(capability_profile_id) if capability_profile_id
            else self.intelligence_repo.get_by_agent(agent_id)
        )
        
        risk_profile = (
            self.risk_repo.get_by_id(risk_profile_id) if risk_profile_id
            else self.risk_repo.get_by_agent(agent_id)
        )
        
        if not risk_profile:
            raise NotFoundError("RiskProfile", f"for agent {agent_id}")
        
        # Determine distribution based on risk
        if custom_distribution:
            distribution = custom_distribution
        else:
            distribution = self._calculate_distribution(risk_profile.overall_risk)
        
        # Calculate total scenarios
        total = risk_profile.recommended_scenario_count
        
        # Calculate tool coverage
        tool_coverage = self._calculate_tool_coverage(risk_profile, capability_profile)
        
        # Create strategy
        strategy = TestStrategy(
            agent_id=agent_id,
            capability_profile_id=capability_profile.id if capability_profile else None,
            risk_profile_id=risk_profile.id,
            name=f"Test Strategy for {risk_profile.overall_risk.upper()} Risk Agent",
            description=f"Automatically generated strategy based on {risk_profile.recommended_test_intensity} testing intensity",
            category_distribution=distribution,
            total_scenario_count=total,
            multi_turn_percentage=30,  # 30% multi-turn
            tool_coverage_targets=tool_coverage,
            risk_coverage_targets=self._calculate_risk_coverage(risk_profile),
            model_used=self.settings.strategy_planning_model,
            generator_version=GENERATOR_VERSION,
        )
        
        self.db.add(strategy)
        self.db.flush()
        self.db.refresh(strategy)
        return strategy

    def _calculate_distribution(self, risk_level: str) -> Dict[str, int]:
        """Calculate category distribution based on risk."""
        distributions = {
            "low": {
                "normal": 40, "edge_case": 20, "ambiguous": 15,
                "adversarial": 10, "safety_critical": 5, "tool_failure": 10
            },
            "medium": {
                "normal": 25, "edge_case": 20, "ambiguous": 15,
                "adversarial": 20, "safety_critical": 10, "tool_failure": 10
            },
            "high": {
                "normal": 20, "edge_case": 15, "ambiguous": 15,
                "adversarial": 25, "safety_critical": 15, "tool_failure": 10
            },
            "critical": {
                "normal": 15, "edge_case": 10, "ambiguous": 10,
                "adversarial": 30, "safety_critical": 25, "tool_failure": 10
            }
        }
        return distributions.get(risk_level, distributions["medium"])

    def _calculate_tool_coverage(self, risk_profile, capability_profile) -> Dict[str, int]:
        """Calculate per-tool scenario targets."""
        tool_coverage = {}
        
        # High-risk tools get more scenarios
        for tool_data in risk_profile.high_risk_tools:
            tool_coverage[tool_data["tool_name"]] = 15
        
        for tool_data in risk_profile.critical_tools:
            tool_coverage[tool_data["tool_name"]] = 25
        
        return tool_coverage

    def _calculate_risk_coverage(self, risk_profile) -> Dict[str, int]:
        """Calculate risk-level coverage targets."""
        return {
            "low": 10,
            "medium": 20,
            "high": 30,
            "critical": 40
        }

    def get_by_id(self, strategy_id: UUID) -> Optional[TestStrategy]:
        """Get strategy by ID."""
        return self.db.query(TestStrategy).filter(TestStrategy.id == strategy_id).first()

    def list_by_agent(self, agent_id: UUID, limit: int = 10):
        """List strategies for agent."""
        return self.db.query(TestStrategy).filter(
            TestStrategy.agent_id == agent_id
        ).limit(limit).all()
