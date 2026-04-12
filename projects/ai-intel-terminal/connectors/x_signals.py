"""
相对路径：projects/ai-intel-terminal/connectors/x_signals.py
文件说明：Twitter/X 行为信号 connector。当前先支持本地 NDJSON fixture，未来可切到 API 或浏览器层。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from .contracts import ConnectorHealth


@dataclass(slots=True)
class RawXSignal:
    source: str
    author: str
    content: str
    timestamp: str
    raw_type: str
    referenced_actor: str = ""
    url: str = ""
    source_url: str = ""
    observed_via: str = "fixture"
    observed_relationship: str = "seed"
    fetch_route: str = ""
    seed_key: str = ""
    metrics: dict[str, float] | None = None
    tags: list[str] | None = None


class XSignalsConnector:
    source_key = "x_people_watch"

    def __init__(self, fixture_path: Path | None = None):
        self.fixture_path = Path(fixture_path) if fixture_path else None

    def fetch_raw(self) -> list[RawXSignal]:
        if not self.fixture_path:
            return []
        rows: list[RawXSignal] = []
        for line in self.fixture_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            rows.append(
                RawXSignal(
                    source=item["source"],
                    author=item["author"],
                    content=item["content"],
                    timestamp=item["timestamp"],
                    raw_type=item["raw_type"],
                    referenced_actor=item.get("referenced_actor", item.get("target_actor", "")),
                    url=item.get("url", item.get("source_url", "")),
                    source_url=item.get("source_url", item.get("url", "")),
                    observed_via=item.get("observed_via", "fixture"),
                    observed_relationship=item.get("observed_relationship", "seed"),
                    fetch_route=item.get("fetch_route", ""),
                    seed_key=item.get("seed_key", ""),
                    metrics=item.get("metrics", {}),
                    tags=item.get("tags", []),
                )
            )
        return rows

    def healthcheck(self) -> ConnectorHealth:
        if self.fixture_path and self.fixture_path.exists():
            return ConnectorHealth.healthy(self.source_key, "fixture source ready")
        return ConnectorHealth.unhealthy(self.source_key, "fixture path missing")


def serialize_x_signals(signals: list[RawXSignal]) -> list[dict[str, object]]:
    return [asdict(signal) for signal in signals]


def raw_signal_from_observed_tweet(tweet: "ObservedTweet") -> RawXSignal:
    return RawXSignal(
        source=tweet.source,
        author=tweet.author,
        content=tweet.content,
        timestamp=tweet.timestamp,
        raw_type=tweet.raw_type,
        referenced_actor=tweet.target_actor,
        url=tweet.source_url,
        source_url=tweet.source_url,
        observed_via=tweet.observed_via,
        observed_relationship=tweet.observed_relationship,
        fetch_route=tweet.fetch_route,
        seed_key=tweet.seed_key,
        metrics=tweet.metrics,
        tags=tweet.tags,
    )
