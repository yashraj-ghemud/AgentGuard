"""Application service for safe agent execution and scenario evaluation."""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from core.execution.http_provider import HTTPExecutionProvider, get_http_provider
from core.execution.provider import ExecutionContext, ExecutionRequest, ExecutionResult
from modules.evaluation.application.evaluator import ScenarioEvaluator
from modules.evaluation.domain.models import EvaluationRun
from modules.evaluation.domain.schemas import EvaluationRequest, EvaluationResponse
from modules.evaluation.infrastructure import EvaluationRunRepository
from shared.exceptions import AgentGuardException
from shared.types import ExecutionStatus


class EvaluationService:
    """Run one scenario through the configured execution provider and score it."""

    def __init__(self, provider: Optional[HTTPExecutionProvider] = None, evaluator: Optional[ScenarioEvaluator] = None, db=None):
        self.provider = provider or get_http_provider()
        self.evaluator = evaluator or ScenarioEvaluator()
        self.repository = EvaluationRunRepository(db) if db is not None else None

    async def execute_and_evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        execution_id = uuid4()
        scenario = request.scenario
        payload: Dict[str, Any] = {request.input_field: scenario.user_input}
        if request.include_conversation and scenario.conversation_steps:
            payload["conversation"] = scenario.conversation_steps

        context = ExecutionContext(
            execution_id=execution_id,
            agent_id=request.agent_id,
            agent_version_id=request.agent_version_id,
            timeout_seconds=request.timeout_seconds,
            metadata={
                "scenario_id": str(scenario.id),
                "agent_id": str(request.agent_id),
                "agent_version_id": str(request.agent_version_id) if request.agent_version_id else None,
                "tags": scenario.tags,
            },
        )
        execution_request = ExecutionRequest(
            context=context,
            endpoint_url=str(request.endpoint_url),
            input_data=payload,
            headers=self._safe_headers(request.headers),
        )

        try:
            execution = await self.provider.execute(execution_request)
        except AgentGuardException as exc:
            execution = ExecutionResult(
                execution_id=execution_id,
                status=self._status_for_exception(exc),
                error_message=exc.message,
                error_code=exc.code,
                metadata={"details": exc.details},
            )

        passed, score, checks, failure_type, severity = self.evaluator.evaluate(execution, scenario)
        response = EvaluationResponse(
            execution_id=execution_id,
            scenario_id=scenario.id,
            status=execution.status.value,
            passed=passed,
            score=score,
            checks=checks,
            failure_type=failure_type,
            severity=severity,
            output_data=execution.output_data,
            error_message=execution.error_message,
            duration_seconds=execution.duration_seconds,
            metadata=self._safe_metadata(execution.metadata),
        )
        self._persist(response, request.agent_id, request.agent_version_id)
        return response

    async def evaluate_execution(self, execution: ExecutionResult, scenario) -> EvaluationResponse:
        """Evaluate an already captured execution for replay and offline workflows."""
        passed, score, checks, failure_type, severity = self.evaluator.evaluate(execution, scenario)
        response = EvaluationResponse(
            execution_id=execution.execution_id,
            scenario_id=scenario.id,
            status=execution.status.value,
            passed=passed,
            score=score,
            checks=checks,
            failure_type=failure_type,
            severity=severity,
            output_data=execution.output_data,
            error_message=execution.error_message,
            duration_seconds=execution.duration_seconds,
            metadata=self._safe_metadata(execution.metadata),
        )
        self._persist(response, execution.metadata.get("agent_id") if execution.metadata else None, execution.metadata.get("agent_version_id") if execution.metadata else None)
        return response

    def _persist(self, response: EvaluationResponse, agent_id, agent_version_id) -> None:
        if self.repository is None or agent_id is None:
            return
        try:
            agent_uuid = agent_id if isinstance(agent_id, UUID) else UUID(str(agent_id))
            version_uuid = None if agent_version_id is None else (agent_version_id if isinstance(agent_version_id, UUID) else UUID(str(agent_version_id)))
            run = EvaluationRun(
                id=response.evaluation_id,
                execution_id=response.execution_id,
                evaluation_id=response.evaluation_id,
                agent_id=agent_uuid,
                agent_version_id=version_uuid,
                scenario_id=response.scenario_id,
                status=response.status,
                passed=1 if response.passed else 0,
                score=response.score,
                failure_type=response.failure_type,
                severity=response.severity,
                duration_seconds=response.duration_seconds,
                checks=[check.model_dump(mode="json") for check in response.checks],
                output_data=response.output_data,
                error_message=response.error_message,
                metadata_json=self._safe_metadata(response.metadata),
            )
            self.repository.create(run)
            self.repository.db.commit()
        except Exception:
            self.repository.db.rollback()
            raise

    @staticmethod
    def _safe_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """Allow caller headers while preventing request identity spoofing."""
        blocked = {
            "host",
            "content-length",
            "connection",
            "transfer-encoding",
            "x-execution-id",
            "x-agent-id",
            "authorization",
            "proxy-authorization",
            "cookie",
        }
        return {
            key: value[:4096]
            for key, value in headers.items()
            if key.lower() not in blocked and len(key) <= 128
        }

    @staticmethod
    def _safe_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Remove response headers that could expose sensitive transport details."""
        cleaned = dict(metadata or {})
        response_headers = cleaned.get("headers")
        if isinstance(response_headers, dict):
            cleaned["headers"] = {
                key: value
                for key, value in response_headers.items()
                if key.lower() not in {"set-cookie", "authorization", "proxy-authorization"}
            }
        return cleaned

    @staticmethod
    def _status_for_exception(exc: AgentGuardException) -> ExecutionStatus:
        if exc.code == "TIMEOUT":
            return ExecutionStatus.TIMEOUT
        return ExecutionStatus.FAILED
