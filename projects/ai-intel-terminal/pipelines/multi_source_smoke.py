"""
相对路径：projects/ai-intel-terminal/pipelines/multi_source_smoke.py
文件说明：本地测试数据驱动的多源 smoke pipeline，接通 RSS/GitHub 与 event_clusters。
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from connectors.github_activity import GitHubActivityConnector
from connectors.rss_news import RSSNewsConnector, serialize_documents
from connectors.x_signals import XSignalsConnector
from delivery.unified_investment_brief import build_unified_investment_brief
from etl.clustering import cluster_events
from pipelines.common import prepare_events, persist_clusters, persist_source_run, write_daily_brief_artifact
from seeds.registry import load_seed_people
from signals.scoring import score_signal
from storage.sqlite_store import SQLiteStore, event_to_dict


def main() -> None:
    fixtures_dir = PROJECT_ROOT / "tests" / "fixtures"
    db_path = PROJECT_ROOT / "data" / "ai_intel_terminal_smoke.db"
    schema_path = PROJECT_ROOT / "data" / "schema.sql"
    seed_path = PROJECT_ROOT / "data" / "seed_persons.json"
    out_dir = PROJECT_ROOT / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)

    store = SQLiteStore(db_path=db_path, schema_path=schema_path)
    store.initialize()
    seed_people = load_seed_people(seed_path)

    rss_connector = FixtureRSSNewsConnector(
        xml_text=(fixtures_dir / "rss_sample.xml").read_text(encoding="utf-8"),
        source_url="fixture://rss-sample",
    )
    github_connector = FixtureGitHubActivityConnector(
        xml_text=(fixtures_dir / "github_sample.xml").read_text(encoding="utf-8"),
        source_url="fixture://github-sample",
    )

    rss_documents = rss_connector.fetch_raw()
    github_documents = github_connector.fetch_raw()
    twitter_raw_signals = XSignalsConnector(fixtures_dir / "x_signals.ndjson").fetch_raw()
    twitter_signals = [
        score_signal(
            signal,
            seed_people=seed_people,
            taxonomy_path=PROJECT_ROOT / "data" / "twitter_signal_taxonomy.json",
            decision_rules_path=PROJECT_ROOT / "data" / "decision_rules.json",
        )
        for signal in twitter_raw_signals
    ]

    rss_source_id = store.upsert_source(
        source_name="AI News RSS Fixture",
        source_type="rss",
        base_url="fixture://rss-sample",
        signal_tier="high",
        access_mode="fixture",
        notes="local smoke data",
    )
    github_source_id = store.upsert_source(
        source_name="GitHub Activity Fixture",
        source_type="github",
        base_url="fixture://github-sample",
        signal_tier="high",
        access_mode="fixture",
        notes="local smoke data",
    )

    persisted_records = []
    for source_id, documents in ((rss_source_id, rss_documents), (github_source_id, github_documents)):
        event_records = prepare_events(documents, seed_people)
        persisted_records.extend(persist_source_run(store, source_id, event_records))

    events = [record["event"] for record in persisted_records]
    clusters = cluster_events(events)
    cluster_rows = persist_clusters(store, persisted_records)

    (out_dir / "multi_source_raw_documents_sample.json").write_text(
        json.dumps(
            serialize_documents(rss_documents) + serialize_documents(github_documents),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / "multi_source_events_sample.json").write_text(
        json.dumps([event_to_dict(record["event"]) for record in persisted_records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "multi_source_clusters_sample.json").write_text(
        json.dumps(cluster_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    artifact_date = date.today().isoformat()
    artifact_path = out_dir / f"{artifact_date}-multi-source-daily-brief-zh.md"
    write_daily_brief_artifact(
        store=store,
        artifact_date=artifact_date,
        title="AI Intel 开发验证日报 - 多源 Smoke",
        source_scope="rss,github",
        events=events,
        clusters=clusters,
        output_path=artifact_path,
        language="zh",
        report_mode="test",
    )
    unified_path = out_dir / f"{artifact_date}-multi-source-investment-brief-zh.md"
    unified_markdown = build_unified_investment_brief(
        rss_events=[record["event"] for record in persisted_records if record["document"].source_key == "ai_news_rss"],
        github_events=[record["event"] for record in persisted_records if record["document"].source_key == "github_org_activity"],
        twitter_signals=twitter_signals,
        title="AI Intel 统一投资结论日报 - 多源 Smoke",
        report_mode="test",
    )
    unified_path.write_text(unified_markdown, encoding="utf-8")
    store.insert_delivery_artifact(
        artifact_type="unified_investment_brief_zh_test",
        artifact_date=artifact_date,
        title="AI Intel 统一投资结论日报 - 多源 Smoke",
        body_markdown=unified_markdown,
        source_scope="rss,github,twitter",
    )
    (out_dir / "multi_source_pipeline_summary.json").write_text(
        json.dumps(
            {
                "db_path": str(db_path),
                "rss_documents": len(rss_documents),
                "github_documents": len(github_documents),
                "persisted_events": len(persisted_records),
                "cluster_count": len(clusters),
                "artifact_path": str(artifact_path),
                "unified_artifact_path": str(unified_path),
                "twitter_signal_count": len(twitter_signals),
                "table_counts": store.summarize_counts(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


class FixtureRSSNewsConnector(RSSNewsConnector):
    def __init__(self, xml_text: str, source_url: str):
        super().__init__([source_url])
        self.xml_text = xml_text
        self.source_url = source_url

    def fetch_raw(self) -> list:
        return self._parse_feed(self.xml_text, self.source_url)


class FixtureGitHubActivityConnector(GitHubActivityConnector):
    def __init__(self, xml_text: str, source_url: str):
        super().__init__([source_url])
        self.xml_text = xml_text
        self.source_url = source_url

    def fetch_raw(self) -> list:
        return self._parse_atom(self.xml_text, self.source_url)


if __name__ == "__main__":
    main()
