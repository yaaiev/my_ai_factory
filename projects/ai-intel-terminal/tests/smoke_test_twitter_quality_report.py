"""
相对路径：projects/ai-intel-terminal/tests/smoke_test_twitter_quality_report.py
文件说明：Twitter/X 质量评估报告 smoke test。
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.twitter_quality_report import main as run_twitter_quality_report


def main() -> None:
    run_twitter_quality_report()
    report = (PROJECT_ROOT / "evidence" / "twitter_observer_quality_report.md").read_text(encoding="utf-8")
    assert "## Evaluate" in report, "quality report missing Evaluate section"
    assert "## Diagnose" in report, "quality report missing Diagnose section"
    assert "## Iterate" in report, "quality report missing Iterate section"
    print("twitter quality report smoke test passed")


if __name__ == "__main__":
    main()
