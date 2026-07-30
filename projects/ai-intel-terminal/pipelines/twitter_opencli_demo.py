"""
相对路径：projects/ai-intel-terminal/pipelines/twitter_opencli_demo.py
文件说明：通过 OpenCLI 获取真实 Twitter/X 数据 -> 信号评分 -> 正式中文日报。
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

from connectors.opencli_twitter import OpenCLITwitterConnector
from connectors.x_signals import serialize_x_signals
from delivery.investment_signal_report import build_investment_signal_report
from pipelines.twitter_observer_demo import load_existing_summary, summary_quality
from seeds.registry import load_seed_people
from signals.scoring import score_signal
from storage.sqlite_store import SQLiteStore


def main() -> None:
    evidence_dir = PROJECT_ROOT / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    db_path = PROJECT_ROOT / "data" / "ai_intel_terminal.db"
    schema_path = PROJECT_ROOT / "data" / "schema.sql"
    seed_path = PROJECT_ROOT / "data" / "seed_persons.json"
    taxonomy_path = PROJECT_ROOT / "data" / "twitter_signal_taxonomy.json"
    decision_rules_path = PROJECT_ROOT / "data" / "decision_rules.json"
    store = SQLiteStore(db_path=db_path, schema_path=schema_path)
    store.initialize()

    connector = OpenCLITwitterConnector()
    health = connector.healthcheck()
    seed_people = [person for person in load_seed_people(seed_path) if person.twitter_handle][:10]
    raw_signals = []
    successful_seeds: list[str] = []
    failed_seeds: dict[str, str] = {}
    profile_samples: list[dict[str, object]] = []
    for seed in seed_people:
        handle = seed.twitter_handle.strip().lstrip("@")
        try:
            profile = connector.fetch_profile(handle)
            if profile:
                profile_samples.append(asdict(profile))
            fetched = connector.fetch_recent_posts(seed=seed, since_days=30, limit=8)
            raw_signals.extend(fetched)
            if fetched:
                successful_seeds.append(seed.name)
        except Exception as exc:
            failed_seeds[seed.name] = str(exc)

    scored_signals = [
        score_signal(
            raw_signal=signal,
            seed_people=seed_people,
            taxonomy_path=taxonomy_path,
            decision_rules_path=decision_rules_path,
        )
        for signal in raw_signals
    ]
    diagnostics = {
        "dependency_ready": True,
        "browser_ready": health.ok,
        "browser_mode": "opencli",
        "preferred_browser_mode": "opencli",
        "resolved_cdp_url": "",
        "successful_seeds": successful_seeds,
        "failed_seeds": failed_seeds,
        "behavior_counts": _count_by(scored_signals, "behavior_type"),
        "route_counts": _count_by(scored_signals, "fetch_route"),
        "discovered_neighbors": [],
        "seed_view_diagnostics": [],
        "notes": [health.detail] if health.detail else [],
    }
    artifact_date = date.today().isoformat()
    report = build_investment_signal_report(
        signals=scored_signals,
        title="AI Intel 投资信号日报 - Twitter/X (OpenCLI)",
        report_mode="formal",
        diagnostics=diagnostics,
    )
    artifact_path = evidence_dir / f"{artifact_date}-twitter-investment-signals-opencli-zh.md"
    artifact_path.write_text(report, encoding="utf-8")
    summary_payload = {
        "db_path": str(db_path),
        "artifact_path": str(artifact_path),
        "seed_count": len(seed_people),
        "observed_signal_count": len(raw_signals),
        "scored_signal_count": len(scored_signals),
        **diagnostics,
    }
    (evidence_dir / "twitter_opencli_pipeline_summary.json").write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (evidence_dir / "twitter_opencli_profiles_sample.json").write_text(
        json.dumps(profile_samples, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (evidence_dir / "twitter_opencli_raw_signals.json").write_text(
        json.dumps(serialize_x_signals(raw_signals), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (evidence_dir / "twitter_opencli_scored_signals.json").write_text(
        json.dumps([asdict(signal) for signal in scored_signals], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    promote_opencli_outputs_if_better(evidence_dir, report, summary_payload, raw_signals, scored_signals)
    store.insert_delivery_artifact(
        artifact_type="twitter_signal_report_zh_formal_opencli",
        artifact_date=artifact_date,
        title="AI Intel 投资信号日报 - Twitter/X (OpenCLI)",
        body_markdown=report,
        source_scope="twitter",
    )


def promote_opencli_outputs_if_better(
    evidence_dir: Path,
    report: str,
    summary_payload: dict[str, object],
    raw_signals,
    scored_signals,
) -> None:
    current_summary_path = evidence_dir / "twitter_observer_pipeline_summary.json"
    current_summary = load_existing_summary(current_summary_path)
    current_quality = summary_quality(current_summary)
    new_quality = summary_quality(summary_payload)
    if new_quality < current_quality:
        return
    artifact_date = date.today().isoformat()
    (evidence_dir / f"{artifact_date}-twitter-investment-signals-formal-zh.md").write_text(report, encoding="utf-8")
    (evidence_dir / "twitter_observer_pipeline_summary.json").write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (evidence_dir / "twitter_observed_raw_signals.json").write_text(
        json.dumps(serialize_x_signals(raw_signals), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (evidence_dir / "twitter_observed_scored_signals.json").write_text(
        json.dumps([asdict(signal) for signal in scored_signals], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _count_by(items, field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = getattr(item, field_name, "") or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


if __name__ == "__main__":
    main()
