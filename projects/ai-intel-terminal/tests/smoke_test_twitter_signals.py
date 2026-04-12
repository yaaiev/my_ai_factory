"""
相对路径：projects/ai-intel-terminal/tests/smoke_test_twitter_signals.py
文件说明：Twitter/X 行为信号 MVP smoke test。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.twitter_signal_smoke import main as run_twitter_signal_smoke


def main() -> None:
    run_twitter_signal_smoke()
    summary = json.loads(
        (PROJECT_ROOT / "evidence" / "twitter_signal_pipeline_summary.json").read_text(encoding="utf-8")
    )
    scored = json.loads(
        (PROJECT_ROOT / "evidence" / "twitter_scored_signals_sample.json").read_text(encoding="utf-8")
    )

    assert summary["raw_signal_count"] >= 5, "twitter raw signal ingestion failed"
    assert summary["scored_signal_count"] >= 5, "twitter signal scoring failed"
    assert any(item["signal_class"] == "infra_expansion" for item in scored), "infra signal missing"
    assert any(item["signal_class"] == "model_release" for item in scored), "model signal missing"
    assert scored[0]["signal_score"] >= 0.5, "top signal score too low"
    print("twitter signal smoke test passed")


if __name__ == "__main__":
    main()
