"""Tests for deterministic scenario evaluation."""

from uuid import uuid4

from core.execution.provider import ExecutionResult
from modules.evaluation.application.evaluator import ScenarioEvaluator
from modules.evaluation.domain.schemas import EvaluationScenario
from shared.types import ExecutionStatus


def scenario(**overrides):
    data = {
        "user_input": "test",
        "expected_behavior": [],
        "validation_rules": [],
    }
    data.update(overrides)
    return EvaluationScenario(**data)


def execution(output_data=None, status=ExecutionStatus.COMPLETED, error_message=None, error_code=None):
    return ExecutionResult(
        execution_id=uuid4(),
        status=status,
        output_data=output_data,
        error_message=error_message,
        error_code=error_code,
    )


def test_must_refuse_passes_and_forbidden_phrase_is_checked():
    passed, score, checks, failure_type, severity = ScenarioEvaluator().evaluate(
        execution({"output": "I cannot assist with that request."}),
        scenario(expected_behavior=[{"behavior_type": "must_refuse", "description": "Refuse"}]),
    )
    assert passed is True
    assert score == 1.0
    assert failure_type is None
    assert severity is None
    assert checks[0].passed is True


def test_must_refuse_fails_when_agent_complies():
    passed, score, checks, failure_type, severity = ScenarioEvaluator().evaluate(
        execution({"output": "Here is the requested sensitive information."}),
        scenario(expected_behavior=[{"behavior_type": "must_refuse", "description": "Refuse"}]),
    )
    assert passed is False
    assert score == 0.0
    assert failure_type == "safety_violation"
    assert severity == "critical"
    assert checks[0].passed is False


def test_tool_use_and_tool_not_use_checks():
    evaluator = ScenarioEvaluator()
    passed, _, _, _, _ = evaluator.evaluate(
        execution({"output": "Done", "tool_calls": [{"name": "search"}]}),
        scenario(expected_behavior=[{"behavior_type": "must_use_tool", "tool_name": "search"}]),
    )
    assert passed is True

    passed, _, _, failure_type, _ = evaluator.evaluate(
        execution({"output": "Done", "tool_calls": [{"name": "delete"}]}),
        scenario(expected_behavior=[{"behavior_type": "must_not_use_tool", "tool_name": "delete"}]),
    )
    assert passed is False
    assert failure_type == "tool_misuse"


def test_validation_rules_support_contains_regex_and_json_path():
    passed, score, checks, _, _ = ScenarioEvaluator().evaluate(
        execution({"output": "Order confirmed: AG-123", "status": "approved"}),
        scenario(
            validation_rules=[
                {"rule_type": "contains", "expected_value": "AG-123", "failure_message": "missing id"},
                {"rule_type": "regex", "expected_value": r"AG-\d+", "failure_message": "bad id"},
                {"rule_type": "json_path_equals", "condition": "status", "expected_value": "approved", "failure_message": "bad status"},
            ]
        ),
    )
    assert passed is True
    assert score == 1.0
    assert all(check.passed for check in checks)


def test_empty_response_fails_without_explicit_expectations():
    passed, score, checks, failure_type, _ = ScenarioEvaluator().evaluate(
        execution({}),
        scenario(),
    )
    assert passed is False
    assert score == 0.0
    assert checks[0].name == "response_present"
    assert failure_type == "empty_response"


def test_execution_failure_is_classified():
    passed, score, checks, failure_type, severity = ScenarioEvaluator().evaluate(
        execution(status=ExecutionStatus.TIMEOUT, error_message="timed out", error_code="TIMEOUT"),
        scenario(),
    )
    assert passed is False
    assert score == 0.0
    assert checks[0].passed is False
    assert failure_type == "timeout"
    assert severity == "critical"


def test_summary_aggregates_pass_rate_and_failure_types():
    summary = ScenarioEvaluator().summarize(
        [
            {"passed": True, "score": 1.0},
            {"passed": False, "score": 0.5, "failure_type": "safety_violation"},
            {"passed": False, "score": 0.0, "failure_type": "timeout"},
        ]
    )
    assert summary == {
        "total": 3,
        "passed": 1,
        "failed": 2,
        "pass_rate": 0.3333,
        "average_score": 0.5,
        "failure_types": {"safety_violation": 1, "timeout": 1},
    }
