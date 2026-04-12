"""
相对路径：projects/ai-intel-terminal/pipelines/unified_investment_demo.py
文件说明：基于本地 fixtures 的 RSS + GitHub + Twitter/X 多源统一投资结论 demo。
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

from connectors.x_signals import XSignalsConnector
from delivery.unified_investment_brief import build_unified_investment_brief
from pipelines.multi_source_smoke import FixtureGitHubActivityConnector, FixtureRSSNewsConnector
from pipelines.common import prepare_events
from seeds.registry import load_seed_people
from signals.scoring import score_signal
from storage.sqlite_store import SQLiteStore


def main() -> None:
    fixtures_dir = PROJECT_ROOT / "tests" / "fixtures"
    db_path = PROJECT_ROOT / "data" / "ai_intel_terminal_unified_smoke.db"
    schema_path = PROJECT_ROOT / "data" / "schema.sql"
    seed_path = PROJECT_ROOT / "data" / "seed_persons.json"
    taxonomy_path = PROJECT_ROOT / "data" / "twitter_signal_taxonomy.json"
    decision_rules_path = PROJECT_ROOT / "data" / "decision_rules.json"
    out_dir = PROJECT_ROOT / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)

    store = SQLiteStore(db_path=db_path, schema_path=schema_path)
    store.initialize()
    seed_people = load_seed_people(seed_path)

    rss_events = [
        event
        for _, event in prepare_events(
            FixtureRSSNewsConnector(
                xml_text=(fixtures_dir / "rss_sample.xml").read_text(encoding="utf-8"),
                source_url="fixture://rss-sample",
            ).fetch_raw(),
            seed_people,
        )
    ]
    github_events = [
        event
        for _, event in prepare_events(
            FixtureGitHubActivityConnector(
                xml_text=(fixtures_dir / "github_sample.xml").read_text(encoding="utf-8"),
                source_url="fixture://github-sample",
            ).fetch_raw(),
            seed_people,
        )
    ]
    twitter_signals = [
        score_signal(signal, seed_people, taxonomy_path, decision_rules_path)
        for signal in XSignalsConnector(fixtures_dir / "x_signals.ndjson").fetch_raw()
    ]

    artifact_date = date.today().isoformat()
    artifact_path = out_dir / f"{artifact_date}-unified-investment-brief-zh.md"
    markdown = build_unified_investment_brief(
        rss_events=rss_events,
        github_events=github_events,
        twitter_signals=twitter_signals,
        title="AI Intel 统一投资结论日报 - 多源 Smoke",
        report_mode="test",
    )
    artifact_path.write_text(markdown, encoding="utf-8")
    store.insert_delivery_artifact(
        artifact_type="unified_investment_brief_zh_test",
        artifact_date=artifact_date,
        title="AI Intel 统一投资结论日报 - 多源 Smoke",
        body_markdown=markdown,
        source_scope="rss,github,twitter",
    )
    (out_dir / "unified_investment_summary.json").write_text(
        json.dumps(
            {
                "artifact_path": str(artifact_path),
                "rss_event_count": len(rss_events),
                "github_event_count": len(github_events),
                "twitter_signal_count": len(twitter_signals),
                "table_counts": store.summarize_counts(),
                "top_twitter_signal": asdict(twitter_signals[0]) if twitter_signals else {},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
