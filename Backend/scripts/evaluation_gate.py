"""CI gate for AgentGuard reliability regression checks.

Usage:
    python scripts/evaluation_gate.py --baseline baseline.json --current current.json

Both files may contain either a ReliabilitySummary object or an EvaluationBatchResponse
object with a nested ``summary`` field.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from modules.evaluation.application.reliability import RegressionDetector
from modules.evaluation.domain.schemas import RegressionRequest, ReliabilitySummary


def load_summary(path: Path) -> ReliabilitySummary:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "summary" in data:
        data = data["summary"]
    return ReliabilitySummary.model_validate(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail CI when AgentGuard reliability regresses")
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--max-pass-rate-drop", type=float, default=0.05)
    parser.add_argument("--max-score-drop", type=float, default=0.05)
    args = parser.parse_args()

    result = RegressionDetector().compare(
        RegressionRequest(
            baseline=load_summary(args.baseline),
            current=load_summary(args.current),
            max_pass_rate_drop=args.max_pass_rate_drop,
            max_score_drop=args.max_score_drop,
        )
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2))
    return 1 if result.regressed else 0


if __name__ == "__main__":
    sys.exit(main())
