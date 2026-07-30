"""
相对路径：projects/ai-intel-terminal/pipelines/rss_news_demo.py
文件说明：RSS -> raw documents -> structured events 的最小演示脚本。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from connectors.rss_news import RSSNewsConnector, serialize_documents
from etl.clustering import cluster_events
from pipelines.common import prepare_events, persist_clusters, persist_source_run, write_daily_brief_artifact
from seeds.registry import load_seed_people
from storage.sqlite_store import SQLiteStore, event_to_dict


DEFAULT_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://blog.google/technology/ai/rss/",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RSS news MVP pipeline.")
    parser.add_argument(
        "--db-path",
        default="data/ai_intel_terminal.db",
        help="SQLite database path relative to project root.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of documents/events to persist.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = PROJECT_ROOT / args.db_path
    schema_path = PROJECT_ROOT / "data" / "schema.sql"
    seed_path = PROJECT_ROOT / "data" / "seed_persons.json"

    store = SQLiteStore(db_path=db_path, schema_path=schema_path)
    store.initialize()
    seed_people = load_seed_people(seed_path)

    connector = RSSNewsConnector(DEFAULT_FEEDS)
    documents = connector.fetch_raw()
    event_records = prepare_events(documents[: args.limit], seed_people)
    events = [event for _, event in event_records]

    source_id = store.upsert_source(
        source_name="AI News RSS",
        source_type="rss",
        base_url=",".join(DEFAULT_FEEDS),
        signal_tier="high",
        access_mode="rss",
        notes="MVP RSS pipeline",
    )

    persisted_records = persist_source_run(store, source_id, event_records)
    cluster_rows = persist_clusters(store, persisted_records)
    clusters = cluster_events(events)

    out_dir = PROJECT_ROOT / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rss_raw_documents_sample.json").write_text(
        json.dumps(serialize_documents([document for document, _ in event_records]), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "rss_structured_events_sample.json").write_text(
        json.dumps([event_to_dict(event) for event in events], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "rss_event_clusters_sample.json").write_text(
        json.dumps(cluster_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    artifact_date = date.today().isoformat()
    artifact_path = out_dir / f"{artifact_date}-rss-daily-brief-zh.md"
    markdown = write_daily_brief_artifact(
        store=store,
        artifact_date=artifact_date,
        title="AI Intel 情报日报 - RSS",
        source_scope="rss",
        events=events,
        clusters=clusters,
        output_path=artifact_path,
        language="zh",
        report_mode="formal",
    )
    (out_dir / "rss_pipeline_run_summary.json").write_text(
        json.dumps(
            {
                "db_path": str(db_path),
                "requested_limit": args.limit,
                "fetched_documents": len(documents),
                "persisted_documents": len(event_records),
                "persisted_events": len(events),
                "cluster_count": len(cluster_rows),
                "matched_people_count": sum(1 for event in events if event.matched_person_keys),
                "persisted_pairs": [
                    {
                        "raw_document_id": record["raw_document_id"],
                        "event_id": record["event_id"],
                        "url": record["document"].url,
                        "event_type": record["event"].event_type,
                        "matched_person_keys": record["event"].matched_person_keys,
                    }
                    for record in persisted_records
                ],
                "artifact_path": str(artifact_path),
                "artifact_preview": markdown[:500],
                "table_counts": store.summarize_counts(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
