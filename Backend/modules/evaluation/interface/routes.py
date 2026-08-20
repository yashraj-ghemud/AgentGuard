"""REST API routes for AgentGuard execution and evaluation."""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, Response, status
from sqlalchemy.orm import Session

from core.database.base import get_db
from modules.evaluation.application.exporters import to_junit_xml, to_sarif
from modules.evaluation.application.reliability import RegressionDetector
from modules.evaluation.application.service import EvaluationService
from modules.evaluation.domain.schemas import (
    EvaluationBatchResponse,
    EvaluationHistoryItem,
    EvaluationRequest,
    EvaluationResponse,
    RegressionRequest,
    RegressionResponse,
    ReliabilitySummary,
)
from modules.evaluation.infrastructure import EvaluationRunRepository

router = APIRouter(prefix="/api/v1/evaluations")
_regression_detector = RegressionDetector()


def get_evaluation_service(db: Session = Depends(get_db)) -> EvaluationService:
    return EvaluationService(db=db)


@router.post(
    "/run",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute and evaluate one scenario",
    description=(
        "Safely execute a red-team scenario against an HTTP agent endpoint and return "
        "explainable behavior and validation checks. Private and metadata networks are blocked by default."
    ),
)
async def run_evaluation(
    request: EvaluationRequest,
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationResponse:
    return await service.execute_and_evaluate(request)


@router.post(
    "/batch",
    response_model=EvaluationBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute and evaluate a bounded batch",
    description="Run up to 25 scenarios sequentially so failures remain isolated and results stay traceable.",
)
async def run_batch(
    requests: List[EvaluationRequest] = Body(..., min_length=1, max_length=25),
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationBatchResponse:
    results: List[EvaluationResponse] = []
    for request in requests:
        results.append(await service.execute_and_evaluate(request))
    summary_dict = service.evaluator.summarize([result.model_dump() for result in results])
    return EvaluationBatchResponse(
        evaluations=results,
        summary=ReliabilitySummary(**summary_dict),
    )


@router.post(
    "/compare",
    response_model=RegressionResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare reliability against a baseline",
    description="Detect score, pass-rate, and safety regressions for CI or release gates.",
)
async def compare_reliability(request: RegressionRequest) -> RegressionResponse:
    return _regression_detector.compare(request)


@router.post("/export/junit", response_class=Response, summary="Export batch results as JUnit XML")
async def export_junit(batch: EvaluationBatchResponse) -> Response:
    return Response(content=to_junit_xml(batch), media_type="application/xml")


@router.post("/export/sarif", response_class=Response, summary="Export batch results as SARIF")
async def export_sarif(batch: EvaluationBatchResponse) -> Response:
    return Response(content=to_sarif(batch), media_type="application/sarif+json")


@router.get(
    "/agents/{agent_id}/history",
    response_model=List[EvaluationHistoryItem],
    summary="List durable evaluation history",
)
def list_evaluation_history(
    agent_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[EvaluationHistoryItem]:
    runs = EvaluationRunRepository(db).list_by_agent(agent_id, limit=limit, offset=offset)
    return [EvaluationHistoryItem.model_validate(run) for run in runs]
