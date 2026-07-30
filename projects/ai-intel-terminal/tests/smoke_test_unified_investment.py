"""
相对路径：projects/ai-intel-terminal/tests/smoke_test_unified_investment.py
文件说明：统一投资结论日报 smoke test。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.unified_investment_demo import main as run_unified_investment_demo


def main() -> None:
    run_unified_investment_demo()
    summary = json.loads((PROJECT_ROOT / "evidence" / "unified_investment_summary.json").read_text(encoding="utf-8"))
    report = (PROJECT_ROOT / "evidence" / "2026-04-12-unified-investment-brief-zh.md").read_text(encoding="utf-8")

    assert summary["rss_event_count"] >= 2, "rss events missing"
    assert summary["github_event_count"] >= 2, "github events missing"
    assert summary["twitter_signal_count"] >= 5, "twitter signals missing"
    assert "今日最强 5 条投资结论" in report, "unified brief missing top conclusions section"
    assert "Twitter/X" in report or "twitter" in report.lower(), "unified brief missing twitter coverage"
    print("unified investment smoke test passed")


if __name__ == "__main__":
    main()
