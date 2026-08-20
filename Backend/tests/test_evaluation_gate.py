"""Tests for the command-line reliability gate."""

import json
from pathlib import Path

from scripts.evaluation_gate import load_summary, main


def write_summary(path: Path, pass_rate: float, average_score: float, failure_types=None):
    path.write_text(
        json.dumps(
            {
                "total": 10,
                "passed": int(pass_rate * 10),
                "failed": 10 - int(pass_rate * 10),
                "pass_rate": pass_rate,
                "average_score": average_score,
                "failure_types": failure_types or {},
            }
        ),
        encoding="utf-8",
    )


def test_load_summary_supports_raw_summary(tmp_path):
    path = tmp_path / "summary.json"
    write_summary(path, 0.9, 0.9)
    assert load_summary(path).pass_rate == 0.9


def test_gate_returns_zero_for_stable_run(tmp_path, monkeypatch):
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    write_summary(baseline, 0.9, 0.9)
    write_summary(current, 0.9, 0.9)
    monkeypatch.setattr("sys.argv", ["evaluation_gate", "--baseline", str(baseline), "--current", str(current)])
    assert main() == 0


def test_gate_returns_one_for_safety_regression(tmp_path, monkeypatch):
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    write_summary(baseline, 0.9, 0.9)
    write_summary(current, 0.9, 0.9, {"safety_violation": 1})
    monkeypatch.setattr("sys.argv", ["evaluation_gate", "--baseline", str(baseline), "--current", str(current)])
    assert main() == 1
