"""CI artifact exporters for evaluation and regression results."""

from __future__ import annotations

import json
from xml.etree.ElementTree import Element, SubElement, tostring

from modules.evaluation.domain.schemas import EvaluationBatchResponse


def to_junit_xml(batch: EvaluationBatchResponse) -> str:
    """Render scenario evaluations as portable JUnit XML."""
    suite = Element(
        "testsuite",
        {
            "name": "AgentGuard evaluations",
            "tests": str(len(batch.evaluations)),
            "failures": str(batch.summary.failed),
            "time": f"{sum(item.duration_seconds or 0 for item in batch.evaluations):.6f}",
        },
    )
    for item in batch.evaluations:
        case = SubElement(
            suite,
            "testcase",
            {
                "name": str(item.scenario_id),
                "classname": f"agentguard.{item.failure_type or 'reliability'}",
                "time": f"{item.duration_seconds or 0:.6f}",
            },
        )
        if not item.passed:
            failure = SubElement(case, "failure", {"type": item.failure_type or "evaluation_failure"})
            failure.text = item.error_message or "; ".join(check.message for check in item.checks if not check.passed)
    return tostring(suite, encoding="unicode")


def to_sarif(batch: EvaluationBatchResponse) -> str:
    """Render failed evaluations as SARIF 2.1.0 results."""
    results = []
    for item in batch.evaluations:
        if item.passed:
            continue
        results.append(
            {
                "ruleId": item.failure_type or "agentguard.evaluation_failure",
                "level": "error" if item.severity in {"critical", "high"} else "warning",
                "message": {
                    "text": item.error_message
                    or "; ".join(check.message for check in item.checks if not check.passed)
                },
                "locations": [{"logicalLocations": [{"fullyQualifiedName": str(item.scenario_id)}]}],
                "properties": {
                    "evaluationId": str(item.evaluation_id),
                    "executionId": str(item.execution_id),
                    "score": item.score,
                    "severity": item.severity,
                },
            }
        )
    return json.dumps(
        {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {"driver": {"name": "AgentGuard", "informationUri": "https://github.com/iamArun24/AgentGuard-Automated-Red-Teaming-Reliability-Testing-for-AI-Agents"}},
                    "results": results,
                }
            ],
        },
        indent=2,
    )
