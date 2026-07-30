"""
相对路径：projects/ai-intel-terminal/pipelines/twitter_signal_smoke.py
文件说明：Twitter/X 行为信号 MVP 的本地 smoke pipeline。
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from connectors.x_signals import XSignalsConnector, serialize_x_signals
from delivery.investment_signal_report import build_investment_signal_report
from seeds.registry import load_seed_people
from signals.scoring import score_signal
from storage.sqlite_store import SQLiteStore


def main() -> None:
    fixture_path = PROJECT_ROOT / "tests" / "fixtures" / "x_signals.ndjson"
    taxonomy_path = PROJECT_ROOT / "data" / "twitter_signal_taxonomy.json"
    decision_rules_path = PROJECT_ROOT / "data" / "decision_rules.json"
    seed_path = PROJECT_ROOT / "data" / "seed_persons.json"
    schema_path = PROJECT_ROOT / "data" / "schema.sql"
    db_path = PROJECT_ROOT / "data" / "ai_intel_terminal_twitter_smoke.db"
    out_dir = PROJECT_ROOT / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)

    store = SQLiteStore(db_path=db_path, schema_path=schema_path)
    store.initialize()
    connector = XSignalsConnector(fixture_path=fixture_path)
    seed_people = load_seed_people(seed_path)
    raw_signals = connector.fetch_raw()
    scored_signals = [
        score_signal(
            raw_signal=signal,
            seed_people=seed_people,
            taxonomy_path=taxonomy_path,
            decision_rules_path=decision_rules_path,
        )
        for signal in raw_signals
    ]

    artifact_date = date.today().isoformat()
    artifact_path = out_dir / f"{artifact_date}-twitter-investment-signals-zh.md"
    markdown = build_investment_signal_report(
        signals=scored_signals,
        title="AI Intel 投资信号日报 - Twitter/X Smoke",
        report_mode="test",
    )
    artifact_path.write_text(markdown, encoding="utf-8")
    store.insert_delivery_artifact(
        artifact_type="twitter_signal_report_zh_test",
        artifact_date=artifact_date,
        title="AI Intel 投资信号日报 - Twitter/X Smoke",
        body_markdown=markdown,
        source_scope="twitter",
    )

    (out_dir / "twitter_raw_signals_sample.json").write_text(
        json.dumps(serialize_x_signals(raw_signals), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "twitter_scored_signals_sample.json").write_text(
        json.dumps([asdict(signal) for signal in scored_signals], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "twitter_signal_pipeline_summary.json").write_text(
        json.dumps(
            {
                "db_path": str(db_path),
                "raw_signal_count": len(raw_signals),
                "scored_signal_count": len(scored_signals),
                "artifact_path": str(artifact_path),
                "table_counts": store.summarize_counts(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
