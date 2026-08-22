"""Contracts for executing and evaluating red-team scenarios."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, model_validator


class GroundingSpec(BaseModel):
    """Reference-grounded checks for hallucination-oriented evaluation.

    The analyzer is intentionally transparent and heuristic: it measures lexical
    support against supplied evidence rather than claiming to prove real-world truth.
    """

    enabled: bool = False
    reference_context: str = Field(default="", max_length=200_000)
    required_facts: List[str] = Field(default_factory=list, max_length=100)
    forbidden_claims: List[str] = Field(default_factory=list, max_length=100)
    answerable: bool = True
    require_abstention_when_unanswerable: bool = True
    min_sentence_overlap: float = Field(default=0.18, ge=0.0, le=1.0)
    max_unsupported_sentences: int = Field(default=0, ge=0, le=100)


class EvaluationScenario(BaseModel):
    """Executable subset of a generated scenario."""

    id: UUID = Field(default_factory=uuid4)
    user_input: str = Field(..., min_length=1, max_length=100_000)
    conversation_steps: List[Dict[str, Any]] = Field(default_factory=list)
    expected_behavior: List[Dict[str, Any]] = Field(default_factory=list)
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    grounding: GroundingSpec = Field(default_factory=GroundingSpec)


class EvaluationRequest(BaseModel):
    """Request to execute one scenario against an HTTP agent endpoint."""

    agent_id: UUID
    agent_version_id: Optional[UUID] = None
    endpoint_url: HttpUrl
    scenario: EvaluationScenario
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    headers: Dict[str, str] = Field(default_factory=dict)
    input_field: str = Field(default="input", min_length=1, max_length=100)
    include_conversation: bool = True


class GroundingRequest(BaseModel):
    """Standalone groundedness check for an already-generated model answer."""

    answer: str = Field(..., min_length=1, max_length=200_000)
    reference_context: str = Field(..., min_length=1, max_length=200_000)
    required_facts: List[str] = Field(default_factory=list, max_length=100)
    forbidden_claims: List[str] = Field(default_factory=list, max_length=100)
    answerable: bool = True
    require_abstention_when_unanswerable: bool = True
    min_sentence_overlap: float = Field(default=0.18, ge=0.0, le=1.0)
    max_unsupported_sentences: int = Field(default=0, ge=0, le=100)


class GroundingEvidence(BaseModel):
    """Explainable evidence for one generated sentence."""

    claim: str
    evidence: Optional[str] = None
    overlap: float = Field(..., ge=0.0, le=1.0)
    supported: bool


class GroundingResponse(BaseModel):
    """Standalone groundedness result with explicit limitations."""

    grounded: bool
    score: float = Field(..., ge=0.0, le=1.0)
    evidence: List[GroundingEvidence]
    unsupported_sentences: List[str]
    missing_required_facts: List[str]
    forbidden_claims_detected: List[str]
    abstention_ok: Optional[bool] = None
    caveat: str


class CheckResult(BaseModel):
    """Result of one expected-behavior or validation-rule check."""

    name: str
    passed: bool
    message: str
    evidence: Optional[Any] = None
    severity: str = "medium"


class EvaluationResponse(BaseModel):
    """Stable response returned after an execution and evaluation."""

    evaluation_id: UUID = Field(default_factory=uuid4)
    execution_id: UUID
    scenario_id: UUID
    status: str
    passed: bool
    score: float = Field(..., ge=0.0, le=1.0)
    checks: List[CheckResult]
    failure_type: Optional[str] = None
    severity: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReliabilitySummary(BaseModel):
    """Aggregate reliability metrics for a batch of evaluations."""

    total: int = Field(..., ge=0)
    passed: int = Field(..., ge=0)
    failed: int = Field(..., ge=0)
    pass_rate: float = Field(..., ge=0.0, le=1.0)
    average_score: float = Field(..., ge=0.0, le=1.0)
    failure_types: Dict[str, int] = Field(default_factory=dict)


class EvaluationBatchRequest(BaseModel):
    """Bounded batch of evaluation requests."""

    requests: List[EvaluationRequest] = Field(..., min_length=1, max_length=25)


class EvaluationBatchResponse(BaseModel):
    """Result for evaluating multiple precomputed execution responses."""

    evaluations: List[EvaluationResponse]
    summary: ReliabilitySummary


class EvaluationHistoryItem(BaseModel):
    """Compact durable evaluation record for history views."""

    id: UUID
    execution_id: UUID
    evaluation_id: UUID
    agent_id: UUID
    agent_version_id: Optional[UUID] = None
    scenario_id: UUID
    status: str
    passed: bool
    score: float
    failure_type: Optional[str] = None
    severity: Optional[str] = None
    duration_seconds: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RegressionRequest(BaseModel):
    """Compare a current run with a trusted baseline."""

    baseline: ReliabilitySummary
    current: ReliabilitySummary
    max_pass_rate_drop: float = Field(default=0.05, ge=0.0, le=1.0)
    max_score_drop: float = Field(default=0.05, ge=0.0, le=1.0)


class RegressionResponse(BaseModel):
    """Explainable regression decision suitable for CI gates."""

    regressed: bool
    severity: str
    baseline_weighted_score: float = Field(..., ge=0.0, le=1.0)
    current_weighted_score: float = Field(..., ge=0.0, le=1.0)
    pass_rate_delta: float
    score_delta: float
    new_failure_types: Dict[str, int] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)


class OutputEnvelope(BaseModel):
    """Convenience contract for common agent response shapes."""

    output: Any = None
    response: Any = None
    text: Any = None
    content: Any = None

    @model_validator(mode="before")
    @classmethod
    def allow_any_mapping(cls, value: Any) -> Any:
        return value if isinstance(value, dict) else {"output": value}
