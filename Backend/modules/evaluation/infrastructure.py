"""Persistence helpers for evaluation runs."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from modules.evaluation.domain.models import EvaluationRun


class EvaluationRunRepository:
    """Small repository focused on durable evaluation history."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, run: EvaluationRun) -> EvaluationRun:
        self.db.add(run)
        self.db.flush()
        self.db.refresh(run)
        return run

    def get(self, run_id: UUID) -> Optional[EvaluationRun]:
        return self.db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()

    def list_by_agent(self, agent_id: UUID, limit: int = 100, offset: int = 0) -> list[EvaluationRun]:
        return (
            self.db.query(EvaluationRun)
            .filter(EvaluationRun.agent_id == agent_id)
            .order_by(EvaluationRun.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_by_version(self, agent_version_id: UUID, limit: int = 100, offset: int = 0) -> list[EvaluationRun]:
        return (
            self.db.query(EvaluationRun)
            .filter(EvaluationRun.agent_version_id == agent_version_id)
            .order_by(EvaluationRun.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
