"""Tests for reliability scoring and regression detection."""

from modules.evaluation.application.reliability import RegressionDetector, ReliabilityScorer
from modules.evaluation.domain.schemas import RegressionRequest, ReliabilitySummary


def summary(**overrides):
    data = {
        "total": 10,
        "passed": 9,
        "failed": 1,
        "pass_rate": 0.9,
        "average_score": 0.92,
        "failure_types": {"behavior_mismatch": 1},
    }
    data.update(overrides)
    return ReliabilitySummary(**data)


def test_weighted_score_is_bounded_and_repeatable():
    value = ReliabilityScorer.weighted_score(summary())
    assert value == 0.908
    assert 0.0 <= value <= 1.0


def test_stable_run_is_not_a_regression():
    result = RegressionDetector().compare(
        RegressionRequest(baseline=summary(), current=summary())
    )
    assert result.regressed is False
    assert result.severity == "none"
    assert result.reasons == []


def test_score_drop_over_threshold_is_high_regression():
    result = RegressionDetector().compare(
        RegressionRequest(
            baseline=summary(),
            current=summary(pass_rate=0.7, passed=7, failed=3, average_score=0.72),
        )
    )
    assert result.regressed is True
    assert result.severity == "high"
    assert result.pass_rate_delta == -0.2
    assert result.score_delta < -0.05


def test_new_safety_failure_escalates_to_critical():
    result = RegressionDetector().compare(
        RegressionRequest(
            baseline=summary(),
            current=summary(
                passed=8,
                failed=2,
                pass_rate=0.8,
                average_score=0.85,
                failure_types={"behavior_mismatch": 1, "safety_violation": 1},
            ),
        )
    )
    assert result.regressed is True
    assert result.severity == "critical"
    assert result.new_failure_types["safety_violation"] == 1
    assert any("Safety violations" in reason for reason in result.reasons)
