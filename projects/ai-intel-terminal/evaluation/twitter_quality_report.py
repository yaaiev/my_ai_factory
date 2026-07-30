"""
相对路径：projects/ai-intel-terminal/evaluation/twitter_quality_report.py
文件说明：基于 Twitter/X observer summary 评估当前情报流质量。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def build_twitter_quality_report(current_summary: dict[str, object], best_summary: dict[str, object]) -> str:
    current_count = int(current_summary.get("observed_signal_count", 0))
    best_count = int(best_summary.get("observed_signal_count", 0))
    behavior_counts = current_summary.get("behavior_counts", {}) or {}
    route_counts = current_summary.get("route_counts", {}) or {}
    seed_view_diagnostics = current_summary.get("seed_view_diagnostics", []) or []
    lines = [
        "# Twitter/X Observer Quality Report",
        "",
        f"- Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"- Current observed signals: {current_count}",
        f"- Best observed signals: {best_count}",
        f"- Preferred browser mode: {current_summary.get('preferred_browser_mode', 'unknown')}",
        f"- Resolved CDP URL: {current_summary.get('resolved_cdp_url', '') or 'not-set'}",
        "",
        "## Evaluate",
        "",
    ]
    if current_count > 0:
        lines.append(f"- Current run produced {current_count} signal(s), which is usable but still below stable-flow expectations.")
    else:
        lines.append("- Current run produced 0 signals, so the current attempt is not yet a stable intelligence flow.")
    if best_count > 0:
        lines.append(f"- Historical best run already captured {best_count} signal(s), proving the pipeline can reach the source under the right environment conditions.")
    else:
        lines.append("- No successful historical run has been preserved yet.")
    non_zero_behaviors = {key: value for key, value in behavior_counts.items() if value}
    if non_zero_behaviors:
        lines.append(f"- Non-zero behavior buckets in the current run: {non_zero_behaviors}.")
    else:
        lines.append("- No behavior bucket produced signals in the current run.")
    non_zero_routes = {key: value for key, value in route_counts.items() if value}
    if non_zero_routes:
        lines.append(f"- Non-zero route buckets in the current run: {non_zero_routes}.")
    else:
        lines.append("- No adapter route produced signals in the current run.")

    lines.extend(["", "## Diagnose", ""])
    if seed_view_diagnostics:
        zero_extract = [item for item in seed_view_diagnostics if not item.get("extracted_count")]
        article_but_zero = [item for item in zero_extract if item.get("article_count", 0) > 0]
        reply_empty = [item for item in zero_extract if item.get("view_name") == "reply"]
        stale_only = [item for item in article_but_zero if item.get("stale_candidate_count", 0) >= item.get("article_count", 0)]
        search_recent = [item for item in seed_view_diagnostics if item.get("view_name") == "tweet_post_search_recent"]
        if article_but_zero:
            lines.append(f"- {len(article_but_zero)} seed/view pages had article cards but still extracted 0 signals, so DOM parsing remains the primary bottleneck.")
        if stale_only:
            lines.append(f"- {len(stale_only)} seed/view pages showed only stale cards outside the observation window, so profile timelines alone are not sufficient.")
        if reply_empty:
            lines.append(f"- {len(reply_empty)} reply pages returned 0 articles, suggesting the `with_replies` route is often inaccessible or differently structured.")
        if search_recent:
            recent_hits = sum(1 for item in search_recent if item.get("extracted_count", 0) > 0)
            lines.append(f"- Search fallback pages checked: {len(search_recent)}, with {recent_hits} pages producing recent-window signals.")
        sample = article_but_zero[:3]
        for item in sample:
            lines.append(
                f"- Sample: {item.get('seed_name')} {item.get('view_name')} | articles={item.get('article_count')} | note={item.get('note')}"
            )
    notes = current_summary.get("notes", []) or []
    for note in notes[:3]:
        lines.append(f"- Runtime note: {note}")

    lines.extend(["", "## Iterate", ""])
    lines.append("- Keep preserving `best` Twitter artifacts so temporary browser failures do not wipe usable signal history.")
    lines.append("- Prioritize `tweet_post` plus `search recent` extraction before `reply` and `like`, because timeline pages already show article cards.")
    lines.append("- Continue reducing dependence on strict timestamp/status selectors and prefer multiple fallback selectors per card.")
    return "\n".join(lines) + "\n"


def main() -> None:
    evidence_dir = PROJECT_ROOT / "evidence"
    current_path = evidence_dir / "twitter_observer_pipeline_summary.json"
    best_path = evidence_dir / "twitter_observer_best_summary.json"
    current = json.loads(current_path.read_text(encoding="utf-8")) if current_path.exists() else {}
    best = json.loads(best_path.read_text(encoding="utf-8")) if best_path.exists() else {}
    report = build_twitter_quality_report(current, best)
    (evidence_dir / "twitter_observer_quality_report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
