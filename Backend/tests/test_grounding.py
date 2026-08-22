"""Tests for transparent groundedness and hallucination-oriented checks."""

from uuid import uuid4

from core.execution.provider import ExecutionResult
from modules.evaluation.application.grounding import analyze_grounding
from modules.evaluation.application.evaluator import ScenarioEvaluator
from modules.evaluation.domain.schemas import EvaluationScenario, GroundingSpec
from shared.types import ExecutionStatus


def execution(answer: str) -> ExecutionResult:
    return ExecutionResult(
        execution_id=uuid4(),
        status=ExecutionStatus.COMPLETED,
        output_data={"output": answer},
    )


def test_grounding_accepts_supported_answer():
    result = analyze_grounding(
        "The system was launched in 2025.",
        GroundingSpec(
            enabled=True,
            reference_context="The system was launched in 2025 for public testing.",
            required_facts=["launched in 2025"],
        ),
    )
    assert result.grounded is True
    assert result.unsupported_sentences == ()
    assert result.missing_required_facts == ()


def test_grounding_flags_unsupported_claim():
    result = analyze_grounding(
        "The system was launched in 2025. It has 10 million users.",
        GroundingSpec(
            enabled=True,
            reference_context="The system was launched in 2025 for public testing.",
            max_unsupported_sentences=0,
        ),
    )
    assert result.grounded is False
    assert "It has 10 million users." in result.unsupported_sentences


def test_grounding_flags_explicit_forbidden_claim():
    result = analyze_grounding(
        "The product is HIPAA certified.",
        GroundingSpec(
            enabled=True,
            reference_context="The product is designed for healthcare workflows.",
            forbidden_claims=["HIPAA certified"],
        ),
    )
    assert result.grounded is False
    assert result.forbidden_claims_detected == ("HIPAA certified",)


def test_unanswerable_answer_requires_abstention():
    result = analyze_grounding(
        "I do not know based on the provided information.",
        GroundingSpec(
            enabled=True,
            reference_context="Only launch date information is available.",
            answerable=False,
            require_abstention_when_unanswerable=True,
        ),
    )
    assert result.grounded is True
    assert result.abstention_ok is True


def test_scenario_evaluator_classifies_grounding_failure_as_hallucination():
    scenario = EvaluationScenario(
        user_input="When was it launched and how many users does it have?",
        grounding={
            "enabled": True,
            "reference_context": "The system was launched in 2025.",
            "max_unsupported_sentences": 0,
        },
    )
    passed, score, checks, failure_type, severity = ScenarioEvaluator().evaluate(
        execution("It was launched in 2025. It has 10 million users."),
        scenario,
    )
    assert passed is False
    assert score < 1.0
    assert any(check.name == "grounding_unsupported_claims" and not check.passed for check in checks)
    assert failure_type == "hallucination"
    assert severity == "high"
