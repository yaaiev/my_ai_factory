"""
相对路径：projects/ai-intel-terminal/tests/smoke_test_multi_source.py
文件说明：多源 smoke test，验证 RSS/GitHub -> events -> clusters 的本地闭环。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.multi_source_smoke import main as run_multi_source_smoke


def main() -> None:
    run_multi_source_smoke()
    summary_path = PROJECT_ROOT / "evidence" / "multi_source_pipeline_summary.json"
    clusters_path = PROJECT_ROOT / "evidence" / "multi_source_clusters_sample.json"
    unified_path = PROJECT_ROOT / "evidence" / "2026-04-12-multi-source-investment-brief-zh.md"

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    clusters = json.loads(clusters_path.read_text(encoding="utf-8"))

    assert summary["rss_documents"] >= 2, "rss fixture ingestion failed"
    assert summary["github_documents"] >= 2, "github fixture ingestion failed"
    assert summary["persisted_events"] >= 4, "event persistence failed"
    assert summary["cluster_count"] >= 2, "event clustering failed"
    assert summary["twitter_signal_count"] >= 5, "twitter signals missing from unified flow"
    assert summary["table_counts"]["event_clusters"] >= 2, "cluster table not populated"
    assert clusters[0]["member_event_ids"], "cluster members missing"
    assert unified_path.exists(), "unified investment brief missing"

    print("multi-source smoke test passed")


if __name__ == "__main__":
    main()
