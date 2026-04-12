"""
相对路径：projects/ai-intel-terminal/tests/smoke_test_unified_real_brief.py
文件说明：基于已有 evidence 的正式统一结论日报 smoke test。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.unified_real_brief import main as run_unified_real_brief


def main() -> None:
    run_unified_real_brief()
    summary = json.loads(
        (PROJECT_ROOT / "evidence" / "unified_investment_formal_summary.json").read_text(encoding="utf-8")
    )
    report_path = PROJECT_ROOT / "evidence" / "2026-04-12-unified-investment-formal-zh.md"
    report = report_path.read_text(encoding="utf-8")

    assert summary["rss_event_count"] >= 1, "rss events missing"
    assert summary["github_event_count"] >= 1, "github events missing"
    assert "今日最强 5 条投资结论" in report, "formal unified report missing headline section"
    assert "https://" in report, "formal unified report missing source links"
    print("unified real brief smoke test passed")


if __name__ == "__main__":
    main()
