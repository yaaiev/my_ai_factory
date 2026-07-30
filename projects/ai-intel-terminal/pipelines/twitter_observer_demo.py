"""
相对路径：projects/ai-intel-terminal/pipelines/twitter_observer_demo.py
文件说明：真实 Twitter/X 浏览器观察层 -> 信号评分 -> 正式报告。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import asdict
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from connectors.x_signals import raw_signal_from_observed_tweet, serialize_x_signals
from delivery.investment_signal_report import build_investment_signal_report
from seeds.registry import load_seed_people
from signals.scoring import score_signal
from sources.catalog import get_source_entry
from storage.sqlite_store import SQLiteStore
from twitter_observer.browser_observer import TwitterBrowserObserver
from twitter_observer.contracts import BrowserObserverConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Twitter/X browser observer pipeline.")
    parser.add_argument("--db-path", default="data/ai_intel_terminal.db")
    parser.add_argument("--seed-limit", type=int, default=10)
    parser.add_argument("--headless", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = PROJECT_ROOT / args.db_path
    schema_path = PROJECT_ROOT / "data" / "schema.sql"
    seed_path = PROJECT_ROOT / "data" / "seed_persons.json"
    taxonomy_path = PROJECT_ROOT / "data" / "twitter_signal_taxonomy.json"
    decision_rules_path = PROJECT_ROOT / "data" / "decision_rules.json"
    source_catalog_path = PROJECT_ROOT / "data" / "source_catalog.json"
    out_dir = PROJECT_ROOT / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)

    store = SQLiteStore(db_path=db_path, schema_path=schema_path)
    store.initialize()
    seed_people = [person for person in load_seed_people(seed_path) if person.twitter_handle][: args.seed_limit]
    source_entry = get_source_entry(source_catalog_path, "x_people_watch")
    resolved_cdp_url = resolve_cdp_url(source_entry)
    resolved_user_data_dir = os.environ.get(
        source_entry.get("browser_user_data_dir_env", "X_BROWSER_USER_DATA_DIR"),
        source_entry.get("browser_user_data_dir", ""),
    )

    config = BrowserObserverConfig(
        base_url=source_entry.get("base_url", "https://x.com"),
        user_data_dir=resolved_user_data_dir if not resolved_cdp_url else "",
        cdp_url=resolved_cdp_url,
        browser_channel=os.environ.get(
            source_entry.get("browser_channel_env", "X_BROWSER_CHANNEL"),
            source_entry.get("browser_channel", "chrome"),
        ),
        headless=_resolve_headless(args.headless),
        observation_window_days=int(source_entry.get("observation_window_days", 7)),
        behavior_types=list(source_entry.get("behavior_types", ["tweet_post", "reply", "retweet", "like"])),
        neighbor_frequency_threshold=int(source_entry.get("neighbor_frequency_threshold", 2)),
        max_items_per_view=int(source_entry.get("max_items_per_view", 10)),
    )

    observer = TwitterBrowserObserver(config=config)
    observed_rows, diagnostics = observer.observe(seed_people)
    raw_signals = [raw_signal_from_observed_tweet(row) for row in observed_rows]
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
    artifact_path = out_dir / f"{artifact_date}-twitter-investment-signals-formal-zh.md"
    diagnostics_dict = {
        "dependency_ready": diagnostics.dependency_ready,
        "browser_ready": diagnostics.browser_ready,
        "browser_mode": "cdp" if config.cdp_url else "persistent_profile",
        "preferred_browser_mode": source_entry.get("preferred_browser_mode", "persistent_profile"),
        "resolved_cdp_url": config.cdp_url,
        "successful_seeds": diagnostics.successful_seeds,
        "failed_seeds": diagnostics.failed_seeds,
        "behavior_counts": diagnostics.behavior_counts,
        "route_counts": diagnostics.route_counts,
        "discovered_neighbors": [asdict(item) for item in diagnostics.discovered_neighbors],
        "seed_view_diagnostics": [asdict(item) for item in diagnostics.seed_view_diagnostics],
        "notes": diagnostics.notes,
    }
    markdown = build_investment_signal_report(
        signals=scored_signals,
        title="AI Intel 投资信号日报 - Twitter/X",
        report_mode="formal",
        diagnostics=diagnostics_dict,
    )
    summary_payload = {
        "db_path": str(db_path),
        "artifact_path": str(artifact_path),
        "seed_count": len(seed_people),
        "observed_signal_count": len(raw_signals),
        "scored_signal_count": len(scored_signals),
        **diagnostics_dict,
    }
    persist_observer_artifacts(
        out_dir=out_dir,
        artifact_path=artifact_path,
        markdown=markdown,
        raw_signals=raw_signals,
        scored_signals=scored_signals,
        summary_payload=summary_payload,
        store=store,
        artifact_date=artifact_date,
    )


def persist_observer_artifacts(
    out_dir: Path,
    artifact_path: Path,
    markdown: str,
    raw_signals,
    scored_signals,
    summary_payload: dict[str, object],
    store: SQLiteStore,
    artifact_date: str,
) -> None:
    summary_path = out_dir / "twitter_observer_pipeline_summary.json"
    best_summary_path = out_dir / "twitter_observer_best_summary.json"
    best_report_path = out_dir / "twitter_observer_best_report.md"
    best_raw_path = out_dir / "twitter_observer_best_raw_signals.json"
    best_scored_path = out_dir / "twitter_observer_best_scored_signals.json"
    existing_summary = load_existing_summary(summary_path)
    existing_best_summary = load_existing_summary(best_summary_path)
    existing_score = summary_quality(existing_summary)
    existing_best_score = summary_quality(existing_best_summary)
    new_score = summary_quality(summary_payload)

    if existing_summary and existing_best_score < existing_score:
        best_summary_path.write_text(
            json.dumps(existing_summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if artifact_path.exists():
            best_report_path.write_text(artifact_path.read_text(encoding="utf-8"), encoding="utf-8")
        raw_current = out_dir / "twitter_observed_raw_signals.json"
        scored_current = out_dir / "twitter_observed_scored_signals.json"
        if raw_current.exists():
            best_raw_path.write_text(raw_current.read_text(encoding="utf-8"), encoding="utf-8")
        if scored_current.exists():
            best_scored_path.write_text(scored_current.read_text(encoding="utf-8"), encoding="utf-8")
        existing_best_score = existing_score

    if existing_score > new_score:
        (out_dir / "twitter_observer_last_attempt_summary.json").write_text(
            json.dumps(summary_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (out_dir / "twitter_observer_last_attempt_report.md").write_text(markdown, encoding="utf-8")
        return

    artifact_path.write_text(markdown, encoding="utf-8")
    store.insert_delivery_artifact(
        artifact_type="twitter_signal_report_zh_formal",
        artifact_date=artifact_date,
        title="AI Intel 投资信号日报 - Twitter/X",
        body_markdown=markdown,
        source_scope="twitter",
    )
    (out_dir / "twitter_observed_raw_signals.json").write_text(
        json.dumps(serialize_x_signals(raw_signals), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "twitter_observed_scored_signals.json").write_text(
        json.dumps([asdict(signal) for signal in scored_signals], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "twitter_observer_debug.json").write_text(
        json.dumps(
            {
                "seed_view_diagnostics": summary_payload.get("seed_view_diagnostics", []),
                "notes": summary_payload.get("notes", []),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    if new_score >= existing_best_score:
        best_summary_path.write_text(
            json.dumps(summary_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        best_report_path.write_text(markdown, encoding="utf-8")
        best_raw_path.write_text(
            json.dumps(serialize_x_signals(raw_signals), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        best_scored_path.write_text(
            json.dumps([asdict(signal) for signal in scored_signals], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def load_existing_summary(summary_path: Path) -> dict[str, object]:
    if not summary_path.exists():
        return {}
    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def summary_quality(summary: dict[str, object]) -> tuple[int, int, int, int, int]:
    if not summary:
        return (0, 0, 0, 0, 0)
    observed = int(summary.get("observed_signal_count", 0))
    browser_ready = 1 if summary.get("browser_ready") else 0
    successful_seeds = len(summary.get("successful_seeds", []) or [])
    view_diagnostics = len(summary.get("seed_view_diagnostics", []) or [])
    article_count = 0
    for item in summary.get("seed_view_diagnostics", []) or []:
        if isinstance(item, dict):
            article_count += int(item.get("article_count", 0))
    return (observed, browser_ready, successful_seeds, view_diagnostics, article_count)


def _resolve_headless(cli_flag: bool) -> bool:
    raw = os.environ.get("X_BROWSER_HEADLESS", "")
    if not raw:
        return cli_flag
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def resolve_cdp_url(source_entry: dict[str, object]) -> str:
    env_key = source_entry.get("browser_cdp_url_env", "X_BROWSER_CDP_URL")
    env_value = os.environ.get(str(env_key), "").strip()
    if env_value:
        return env_value
    preferred = str(source_entry.get("preferred_browser_mode", "")).strip().lower()
    default_cdp_url = str(source_entry.get("default_cdp_url", "")).strip()
    if preferred == "cdp" and default_cdp_url and cdp_endpoint_ready(default_cdp_url):
        return default_cdp_url
    return str(source_entry.get("browser_cdp_url", "")).strip()


def cdp_endpoint_ready(base_url: str) -> bool:
    probe_url = base_url.rstrip("/") + "/json/version"
    try:
        with urllib.request.urlopen(probe_url, timeout=1.5) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


if __name__ == "__main__":
    main()
