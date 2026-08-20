"""Tests for CI artifact exporters."""

import json
import xml.etree.ElementTree as ET
from uuid import uuid4

from modules.evaluation.application.exporters import to_junit_xml, to_sarif
from modules.evaluation.domain.schemas import (
    CheckResult,
    EvaluationBatchResponse,
    EvaluationResponse,
    ReliabilitySummary,
)


def make_batch():
    failed = EvaluationResponse(
        execution_id=uuid4(),
        scenario_id=uuid4(),
        status="completed",
        passed=False,
        score=0.0,
        checks=[CheckResult(name="refusal", passed=False, message="Expected refusal")],
        failure_type="safety_violation",
        severity="critical",
    )
    passed = EvaluationResponse(
        execution_id=uuid4(),
        scenario_id=uuid4(),
        status="completed",
        passed=True,
        score=1.0,
        checks=[CheckResult(name="response", passed=True, message="Response present")],
    )
    return EvaluationBatchResponse(
        evaluations=[failed, passed],
        summary=ReliabilitySummary(
            total=2,
            passed=1,
            failed=1,
            pass_rate=0.5,
            average_score=0.5,
            failure_types={"safety_violation": 1},
        ),
    )


def test_junit_contains_all_cases_and_failed_assertion():
    root = ET.fromstring(to_junit_xml(make_batch()))
    assert root.tag == "testsuite"
    assert root.attrib["tests"] == "2"
    assert len(root.findall("testcase")) == 2
    assert root.find("testcase/failure") is not None


def test_sarif_contains_only_failed_results_and_required_version():
    payload = json.loads(to_sarif(make_batch()))
    assert payload["version"] == "2.1.0"
    assert payload["runs"][0]["tool"]["driver"]["name"] == "AgentGuard"
    assert len(payload["runs"][0]["results"]) == 1
    assert payload["runs"][0]["results"][0]["ruleId"] == "safety_violation"
