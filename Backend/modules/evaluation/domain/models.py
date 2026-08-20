"""Persistent models for evaluation runs and explainable results."""

from __future__ import annotations

from sqlalchemy import Column, Float, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from core.database.base import BaseModel


class EvaluationRun(BaseModel):
    """One durable evaluation result linked to an agent and scenario."""

    __tablename__ = "evaluation_runs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    execution_id = Column(PGUUID(as_uuid=True), nullable=False, unique=True)
    evaluation_id = Column(PGUUID(as_uuid=True), nullable=False, unique=True)
    agent_id = Column(PGUUID(as_uuid=True), nullable=False)
    agent_version_id = Column(PGUUID(as_uuid=True), nullable=True)
    scenario_id = Column(PGUUID(as_uuid=True), nullable=False)
    status = Column(String(32), nullable=False)
    passed = Column(Integer, nullable=False, default=0)
    score = Column(Float, nullable=False, default=0.0)
    failure_type = Column(String(64), nullable=True)
    severity = Column(String(32), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    checks = Column(JSONB, nullable=False, default=list)
    output_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_evaluation_runs_agent_id", "agent_id"),
        Index("idx_evaluation_runs_agent_version_id", "agent_version_id"),
        Index("idx_evaluation_runs_scenario_id", "scenario_id"),
        Index("idx_evaluation_runs_created_at", "created_at"),
        Index("idx_evaluation_runs_failure_type", "failure_type"),
    )
