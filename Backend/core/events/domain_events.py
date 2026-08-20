"""
Domain event definitions.

This module defines all domain events that can be published in the system.
Each module can define its own events, but they should be registered here
for discoverability.
"""
from typing import Any, Dict, Optional
from uuid import UUID

from core.events.base import DomainEvent


# ============================================================================
# Agent Registry Events
# ============================================================================

class AgentCreated(DomainEvent):
    """Event published when an agent is created."""
    event_type: str = "agent.created"
    agent_id: UUID
    agent_name: str
    workspace_id: Optional[UUID] = None


class AgentUpdated(DomainEvent):
    """Event published when an agent is updated."""
    event_type: str = "agent.updated"
    agent_id: UUID
    agent_name: str
    changes: Dict[str, Any]
    workspace_id: Optional[UUID] = None


class AgentDeleted(DomainEvent):
    """Event published when an agent is deleted."""
    event_type: str = "agent.deleted"
    agent_id: UUID
    agent_name: str
    workspace_id: Optional[UUID] = None


# ============================================================================
# Agent Versioning Events
# ============================================================================

class AgentVersionCreated(DomainEvent):
    """Event published when an agent version is created."""
    event_type: str = "agent_version.created"
    agent_id: UUID
    version_id: UUID
    version_number: str
    workspace_id: Optional[UUID] = None


# ============================================================================
# Tool Registry Events
# ============================================================================

class ToolRegistered(DomainEvent):
    """Event published when a tool is registered."""
    event_type: str = "tool.registered"
    tool_id: UUID
    tool_name: str
    agent_id: UUID
    risk_level: str
    workspace_id: Optional[UUID] = None


class ToolUpdated(DomainEvent):
    """Event published when a tool is updated."""
    event_type: str = "tool.updated"
    tool_id: UUID
    tool_name: str
    agent_id: UUID
    changes: Dict[str, Any]
    workspace_id: Optional[UUID] = None


class ToolDeleted(DomainEvent):
    """Event published when a tool is deleted."""
    event_type: str = "tool.deleted"
    tool_id: UUID
    tool_name: str
    agent_id: UUID
    workspace_id: Optional[UUID] = None


# ============================================================================
# Future Events (Placeholders for Part 2+)
# ============================================================================

class EvaluationRequested(DomainEvent):
    """Event published when an evaluation is requested."""
    event_type: str = "evaluation.requested"
    evaluation_id: UUID
    agent_id: UUID
    scenario_id: UUID


class EvaluationStarted(DomainEvent):
    """Event published when an evaluation starts."""
    event_type: str = "evaluation.started"
    evaluation_id: UUID
    agent_id: UUID


class ExecutionStarted(DomainEvent):
    """Event published when an execution starts."""
    event_type: str = "execution.started"
    execution_id: UUID
    agent_id: UUID
    scenario_id: UUID


class ExecutionCompleted(DomainEvent):
    """Event published when an execution completes successfully."""
    event_type: str = "execution.completed"
    execution_id: UUID
    agent_id: UUID
    scenario_id: UUID
    duration_seconds: float


class ExecutionFailed(DomainEvent):
    """Event published when an execution fails."""
    event_type: str = "execution.failed"
    execution_id: UUID
    agent_id: UUID
    scenario_id: UUID
    error_message: str


class TraceCreated(DomainEvent):
    """Event published when a trace is created."""
    event_type: str = "trace.created"
    trace_id: UUID
    execution_id: UUID


class EvaluationCompleted(DomainEvent):
    """Event published when an evaluation completes."""
    event_type: str = "evaluation.completed"
    evaluation_id: UUID
    agent_id: UUID
    passed: bool
    score: Optional[float] = None


class FailureDetected(DomainEvent):
    """Event published when a failure is detected."""
    event_type: str = "failure.detected"
    failure_id: UUID
    execution_id: UUID
    failure_type: str
    severity: str


class ScoreCalculated(DomainEvent):
    """Event published when a reliability score is calculated."""
    event_type: str = "score.calculated"
    agent_id: UUID
    score: float
    version_id: Optional[UUID] = None


class RegressionDetected(DomainEvent):
    """Event published when a regression is detected."""
    event_type: str = "regression.detected"
    agent_id: UUID
    old_version_id: UUID
    new_version_id: UUID
    regression_type: str
    severity: str
