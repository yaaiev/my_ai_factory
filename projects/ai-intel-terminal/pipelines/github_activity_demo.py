"""
相对路径：projects/ai-intel-terminal/pipelines/github_activity_demo.py
文件说明：GitHub Atom feed -> events -> clusters -> daily brief 的真实 demo。
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

from connectors.github_activity import GitHubActivityConnector
from connectors.rss_news import serialize_documents
from delivery.daily_brief import build_daily_brief
from etl.clustering import cluster_events
from pipelines.common import prepare_events, persist_clusters, persist_source_run
from seeds.registry import load_seed_people
from sources.catalog import get_source_entry
from storage.sqlite_store import SQLiteStore, event_to_dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the GitHub activity MVP pipeline.")
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
    source_catalog_path = PROJECT_ROOT / "data" / "source_catalog.json"
    out_dir = PROJECT_ROOT / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)

    store = SQLiteStore(db_path=db_path, schema_path=schema_path)
    store.initialize()
    seed_people = load_seed_people(seed_path)
    source_entry = get_source_entry(source_catalog_path, "github_org_activity")
    feed_urls = list(source_entry.get("feed_urls", []))

    connector = GitHubActivityConnector(feed_urls)
    documents, feed_diagnostics = connector.fetch_raw_with_diagnostics()
    event_records = prepare_events(documents[: args.limit], seed_people)
    events = [event for _, event in event_records]

    source_id = store.upsert_source(
        source_name=source_entry.get("source_name", "GitHub Activity"),
        source_type=source_entry.get("source_type", "github"),
        base_url=",".join(feed_urls),
        signal_tier=source_entry.get("signal_tier", "high"),
        access_mode=source_entry.get("access_mode", "atom"),
        notes=source_entry.get("notes", "MVP GitHub atom pipeline"),
    )

    persisted_records = persist_source_run(store, source_id, event_records)
    cluster_rows = persist_clusters(store, persisted_records)
    clusters = cluster_events(events)
    artifact_date = date.today().isoformat()
    markdown = build_daily_brief(
        events=events,
        clusters=clusters,
        title="AI Intel 情报日报 - GitHub",
        language="zh",
        report_mode="formal",
    )
    markdown = append_github_diagnostics(markdown, feed_diagnostics, not documents)
    artifact_path = out_dir / f"{artifact_date}-github-daily-brief-zh.md"
    artifact_path.write_text(markdown, encoding="utf-8")
    store.insert_delivery_artifact(
        artifact_type="daily_brief_zh_formal",
        artifact_date=artifact_date,
        title="AI Intel 情报日报 - GitHub",
        body_markdown=markdown,
        source_scope="github",
    )

    (out_dir / "github_raw_documents_sample.json").write_text(
        json.dumps(serialize_documents([record["document"] for record in persisted_records]), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "github_structured_events_sample.json").write_text(
        json.dumps([event_to_dict(event) for event in events], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "github_event_clusters_sample.json").write_text(
        json.dumps(cluster_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "github_pipeline_run_summary.json").write_text(
        json.dumps(
            {
                "db_path": str(db_path),
                "requested_limit": args.limit,
                "feed_urls": feed_urls,
                "feed_fetch_results": feed_diagnostics,
                "fetch_errors": [row for row in feed_diagnostics if not row["ok"]],
                "fetched_documents": len(documents),
                "persisted_documents": len(event_records),
                "persisted_events": len(events),
                "cluster_count": len(cluster_rows),
                "artifact_path": str(artifact_path),
                "table_counts": store.summarize_counts(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def append_github_diagnostics(
    markdown: str,
    feed_diagnostics: list[dict[str, object]],
    documents_empty: bool,
) -> str:
    lines = [markdown.rstrip(), "", "## GitHub 源诊断", ""]
    if documents_empty:
        lines.append("- 本轮为空不是“无事发生”，而是“本轮源抓取为空，需调整 feed 或检查网络/访问限制”。")
    for row in feed_diagnostics:
        status = "ok" if row["ok"] else "error"
        detail = f"error={row['error']}" if row["error"] else f"documents={row['document_count']}"
        lines.append(f"- `{status}` | {row['feed_url']} | {detail}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
