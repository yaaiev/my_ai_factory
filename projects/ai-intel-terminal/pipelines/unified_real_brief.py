"""
相对路径：projects/ai-intel-terminal/pipelines/unified_real_brief.py
文件说明：基于本地真实 evidence 产出统一正式投资结论日报。
"""
from __future__ import annotations

import json
import sys
from dataclasses import fields
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from connectors.x_signals import RawXSignal
from delivery.unified_investment_brief import build_unified_investment_brief
from etl.contracts import StructuredEvent
from seeds.registry import load_seed_people
from signals.contracts import ScoredSignal
from signals.scoring import score_signal
from storage.sqlite_store import SQLiteStore


def main() -> None:
    evidence_dir = PROJECT_ROOT / "evidence"
    schema_path = PROJECT_ROOT / "data" / "schema.sql"
    db_path = PROJECT_ROOT / "data" / "ai_intel_terminal.db"
    seed_path = PROJECT_ROOT / "data" / "seed_persons.json"
    taxonomy_path = PROJECT_ROOT / "data" / "twitter_signal_taxonomy.json"
    decision_rules_path = PROJECT_ROOT / "data" / "decision_rules.json"
    store = SQLiteStore(db_path=db_path, schema_path=schema_path)
    store.initialize()

    rss_events = load_structured_events(evidence_dir / "rss_structured_events_sample.json")
    github_events = load_structured_events(evidence_dir / "github_structured_events_sample.json")
    twitter_signals = load_or_rescore_twitter_signals(
        scored_path=evidence_dir / "twitter_observed_scored_signals.json",
        raw_path=evidence_dir / "twitter_observed_raw_signals.json",
        best_scored_path=evidence_dir / "twitter_observer_best_scored_signals.json",
        best_raw_path=evidence_dir / "twitter_observer_best_raw_signals.json",
        opencli_scored_path=evidence_dir / "twitter_opencli_scored_signals.json",
        opencli_raw_path=evidence_dir / "twitter_opencli_raw_signals.json",
        seed_path=seed_path,
        taxonomy_path=taxonomy_path,
        decision_rules_path=decision_rules_path,
    )

    artifact_date = date.today().isoformat()
    artifact_path = evidence_dir / f"{artifact_date}-unified-investment-formal-zh.md"
    markdown = build_unified_investment_brief(
        rss_events=rss_events,
        github_events=github_events,
        twitter_signals=twitter_signals,
        title="AI Intel 统一投资结论日报 - 正式版",
        report_mode="formal",
    )
    artifact_path.write_text(markdown, encoding="utf-8")
    store.insert_delivery_artifact(
        artifact_type="unified_investment_brief_zh_formal",
        artifact_date=artifact_date,
        title="AI Intel 统一投资结论日报 - 正式版",
        body_markdown=markdown,
        source_scope="rss,github,twitter",
    )
    (evidence_dir / "unified_investment_formal_summary.json").write_text(
        json.dumps(
            {
                "artifact_path": str(artifact_path),
                "rss_event_count": len(rss_events),
                "github_event_count": len(github_events),
                "twitter_signal_count": len(twitter_signals),
                "table_counts": store.summarize_counts(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_structured_events(path: Path) -> list[StructuredEvent]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    event_field_names = {field.name for field in fields(StructuredEvent)}
    events: list[StructuredEvent] = []
    for item in payload:
        normalized = {
            "signal_strength_score": 0.5,
            "research_priority": "medium",
            **{key: value for key, value in item.items() if key in event_field_names},
        }
        events.append(StructuredEvent(**normalized))
    return events


def load_scored_signals(path: Path) -> list[ScoredSignal]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    signal_field_names = {field.name for field in fields(ScoredSignal)}
    signals: list[ScoredSignal] = []
    for item in payload:
        normalized = {
            "target_actor": "",
            "observed_via": "",
            "observed_relationship": "seed",
            "fetch_route": "",
            "research_reason_zh": "",
            "score_breakdown": {},
            "tags": [],
            **{key: value for key, value in item.items() if key in signal_field_names},
        }
        signals.append(ScoredSignal(**normalized))
    return signals


def load_or_rescore_twitter_signals(
    scored_path: Path,
    raw_path: Path,
    best_scored_path: Path,
    best_raw_path: Path,
    opencli_scored_path: Path,
    opencli_raw_path: Path,
    seed_path: Path,
    taxonomy_path: Path,
    decision_rules_path: Path,
) -> list[ScoredSignal]:
    scored_signals = load_scored_signals(scored_path)
    if scored_signals:
        return scored_signals
    scored_signals = load_scored_signals(opencli_scored_path)
    if scored_signals:
        return scored_signals
    scored_signals = load_scored_signals(best_scored_path)
    if scored_signals:
        return scored_signals
    if not raw_path.exists():
        if opencli_raw_path.exists():
            raw_path = opencli_raw_path
        else:
            raw_path = best_raw_path
    if not raw_path.exists():
        return []
    seed_people = load_seed_people(seed_path)
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    raw_signals = [
        RawXSignal(
            source=item.get("source", "twitter"),
            author=item.get("author", ""),
            content=item.get("content", ""),
            timestamp=item.get("timestamp", ""),
            raw_type=item.get("raw_type", ""),
            referenced_actor=item.get("referenced_actor", ""),
            url=item.get("url", item.get("source_url", "")),
            source_url=item.get("source_url", item.get("url", "")),
            observed_via=item.get("observed_via", "browser_observer"),
            observed_relationship=item.get("observed_relationship", "seed"),
            fetch_route=item.get("fetch_route", ""),
            seed_key=item.get("seed_key", ""),
            metrics=item.get("metrics", {}),
            tags=item.get("tags", []),
        )
        for item in payload
    ]
    return [
        score_signal(
            raw_signal=raw_signal,
            seed_people=seed_people,
            taxonomy_path=taxonomy_path,
            decision_rules_path=decision_rules_path,
        )
        for raw_signal in raw_signals
    ]


if __name__ == "__main__":
    main()
