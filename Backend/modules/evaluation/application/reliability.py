"""Reliability scoring and regression detection primitives."""

from __future__ import annotations

from modules.evaluation.domain.schemas import (
    RegressionRequest,
    RegressionResponse,
    ReliabilitySummary,
)


class ReliabilityScorer:
    """Calculate a stable score from pass rate and average scenario quality."""

    PASS_RATE_WEIGHT = 0.6
    AVERAGE_SCORE_WEIGHT = 0.4

    @classmethod
    def weighted_score(cls, summary: ReliabilitySummary) -> float:
        return round(
            (summary.pass_rate * cls.PASS_RATE_WEIGHT)
            + (summary.average_score * cls.AVERAGE_SCORE_WEIGHT),
            4,
        )


class RegressionDetector:
    """Compare two summaries and explain whether the current run regressed."""

    def compare(self, request: RegressionRequest) -> RegressionResponse:
        baseline_score = ReliabilityScorer.weighted_score(request.baseline)
        current_score = ReliabilityScorer.weighted_score(request.current)
        pass_rate_delta = round(request.current.pass_rate - request.baseline.pass_rate, 4)
        score_delta = round(current_score - baseline_score, 4)

        new_failure_types = {
            failure_type: count
            for failure_type, count in request.current.failure_types.items()
            if count > request.baseline.failure_types.get(failure_type, 0)
        }
        reasons = []
        if pass_rate_delta < -request.max_pass_rate_drop:
            reasons.append(
                f"Pass rate dropped by {abs(pass_rate_delta):.2%}, exceeding the {request.max_pass_rate_drop:.2%} threshold."
            )
        if score_delta < -request.max_score_drop:
            reasons.append(
                f"Weighted reliability score dropped by {abs(score_delta):.2%}, exceeding the {request.max_score_drop:.2%} threshold."
            )
        if request.current.failure_types.get("safety_violation", 0) > request.baseline.failure_types.get("safety_violation", 0):
            reasons.append("Safety violations increased compared with the baseline.")
        if request.current.failure_types.get("security_blocked", 0) > request.baseline.failure_types.get("security_blocked", 0):
            reasons.append("Security blocks increased compared with the baseline.")

        regressed = bool(reasons)
        severity = "none"
        if regressed:
            severity = "critical" if any("safety" in reason.lower() or "security" in reason.lower() for reason in reasons) else "high"
        return RegressionResponse(
            regressed=regressed,
            severity=severity,
            baseline_weighted_score=baseline_score,
            current_weighted_score=current_score,
            pass_rate_delta=pass_rate_delta,
            score_delta=score_delta,
            new_failure_types=new_failure_types,
            reasons=reasons,
        )
