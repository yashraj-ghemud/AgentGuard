"""
Scenario Generation Infrastructure - Repository

Database operations for scenarios, suites, and generation runs.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from modules.scenario_generation.domain.models import (
    ScenarioSuite,
    Scenario,
    ScenarioGenerationRun,
)


class ScenarioRepository:
    """Repository for scenario database operations."""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # Scenario Suite Operations
    # ========================================================================

    def create_suite(self, suite: ScenarioSuite) -> ScenarioSuite:
        """Create a new scenario suite."""
        self.db.add(suite)
        self.db.commit()
        self.db.refresh(suite)
        return suite

    def get_suite(self, suite_id: UUID) -> Optional[ScenarioSuite]:
        """Get suite by ID."""
        return self.db.query(ScenarioSuite).filter(ScenarioSuite.id == suite_id).first()

    def get_suites_by_agent(
        self,
        agent_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[ScenarioSuite]:
        """Get all suites for an agent."""
        return (
            self.db.query(ScenarioSuite)
            .filter(ScenarioSuite.agent_id == agent_id)
            .order_by(desc(ScenarioSuite.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_suites_by_version(
        self,
        agent_version_id: UUID,
        limit: int = 50
    ) -> List[ScenarioSuite]:
        """Get all suites for an agent version."""
        return (
            self.db.query(ScenarioSuite)
            .filter(ScenarioSuite.agent_version_id == agent_version_id)
            .order_by(desc(ScenarioSuite.created_at))
            .limit(limit)
            .all()
        )

    def update_suite(self, suite: ScenarioSuite) -> ScenarioSuite:
        """Update suite."""
        suite.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(suite)
        return suite

    def lock_suite(self, suite_id: UUID) -> bool:
        """Lock a suite to make it immutable."""
        suite = self.get_suite(suite_id)
        if not suite:
            return False
        
        suite.is_locked = True
        suite.locked_at = datetime.utcnow()
        suite.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def delete_suite(self, suite_id: UUID) -> bool:
        """Delete a suite (only if unlocked)."""
        suite = self.get_suite(suite_id)
        if not suite or suite.is_locked:
            return False
        
        self.db.delete(suite)
        self.db.commit()
        return True

    # ========================================================================
    # Scenario Operations
    # ========================================================================

    def create_scenario(self, scenario: Scenario) -> Scenario:
        """Create a new scenario."""
        self.db.add(scenario)
        self.db.commit()
        self.db.refresh(scenario)
        return scenario

    def bulk_create_scenarios(self, scenarios: List[Scenario]) -> List[Scenario]:
        """Bulk create scenarios."""
        self.db.add_all(scenarios)
        self.db.commit()
        for scenario in scenarios:
            self.db.refresh(scenario)
        return scenarios

    def get_scenario(self, scenario_id: UUID) -> Optional[Scenario]:
        """Get scenario by ID."""
        return self.db.query(Scenario).filter(Scenario.id == scenario_id).first()

    def get_scenarios_by_suite(
        self,
        suite_id: UUID,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 500
    ) -> List[Scenario]:
        """Get scenarios in a suite with optional filters."""
        query = self.db.query(Scenario).filter(Scenario.scenario_suite_id == suite_id)
        
        if category:
            query = query.filter(Scenario.category == category)
        if priority:
            query = query.filter(Scenario.priority == priority)
        
        return query.order_by(Scenario.priority, Scenario.created_at).limit(limit).all()

    def get_scenarios_by_agent_version(
        self,
        agent_version_id: UUID,
        limit: int = 500
    ) -> List[Scenario]:
        """Get all scenarios for an agent version."""
        return (
            self.db.query(Scenario)
            .filter(Scenario.agent_version_id == agent_version_id)
            .order_by(desc(Scenario.created_at))
            .limit(limit)
            .all()
        )

    def update_scenario(self, scenario: Scenario) -> Scenario:
        """Update scenario."""
        scenario.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(scenario)
        return scenario

    def delete_scenario(self, scenario_id: UUID) -> bool:
        """Delete a scenario."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return False
        
        self.db.delete(scenario)
        self.db.commit()
        return True

    def mark_as_duplicate(
        self,
        scenario_id: UUID,
        duplicate_of_id: UUID
    ) -> bool:
        """Mark a scenario as duplicate of another."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return False
        
        scenario.is_duplicate = True
        scenario.duplicate_of_id = duplicate_of_id
        scenario.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    # ========================================================================
    # Generation Run Operations
    # ========================================================================

    def create_generation_run(self, run: ScenarioGenerationRun) -> ScenarioGenerationRun:
        """Create a new generation run."""
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_generation_run(self, run_id: UUID) -> Optional[ScenarioGenerationRun]:
        """Get generation run by ID."""
        return self.db.query(ScenarioGenerationRun).filter(
            ScenarioGenerationRun.id == run_id
        ).first()

    def get_generation_runs_by_agent(
        self,
        agent_id: UUID,
        limit: int = 50
    ) -> List[ScenarioGenerationRun]:
        """Get generation runs for an agent."""
        return (
            self.db.query(ScenarioGenerationRun)
            .filter(ScenarioGenerationRun.agent_id == agent_id)
            .order_by(desc(ScenarioGenerationRun.created_at))
            .limit(limit)
            .all()
        )

    def update_generation_run(self, run: ScenarioGenerationRun) -> ScenarioGenerationRun:
        """Update generation run."""
        run.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)
        return run

    def update_run_progress(
        self,
        run_id: UUID,
        status: Optional[str] = None,
        phase: Optional[str] = None,
        scenarios_generated: Optional[int] = None,
        scenarios_validated: Optional[int] = None,
        scenarios_rejected: Optional[int] = None,
        llm_calls: Optional[int] = None,
        estimated_cost: Optional[float] = None
    ) -> bool:
        """Update generation run progress."""
        run = self.get_generation_run(run_id)
        if not run:
            return False
        
        if status:
            run.status = status
        if phase:
            run.current_phase = phase
        if scenarios_generated is not None:
            run.scenarios_generated = scenarios_generated
        if scenarios_validated is not None:
            run.scenarios_validated = scenarios_validated
        if scenarios_rejected is not None:
            run.scenarios_rejected = scenarios_rejected
        if llm_calls is not None:
            run.total_llm_calls = llm_calls
        if estimated_cost is not None:
            run.estimated_cost = estimated_cost
        
        run.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def complete_generation_run(
        self,
        run_id: UUID,
        success: bool = True,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark generation run as complete."""
        run = self.get_generation_run(run_id)
        if not run:
            return False
        
        run.status = "completed" if success else "failed"
        run.completed_at = datetime.utcnow()
        
        if run.started_at:
            duration = (run.completed_at - run.started_at).total_seconds()
            run.duration_seconds = duration
        
        if error_message:
            run.error_message = error_message
        if error_details:
            run.error_details = error_details
        
        run.updated_at = datetime.utcnow()
        self.db.commit()
        return True
