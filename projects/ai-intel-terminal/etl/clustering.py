"""
相对路径：projects/ai-intel-terminal/etl/clustering.py
文件说明：MVP 事件聚类模块，按人物/事件类型/主题做轻量聚合。
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from .contracts import StructuredEvent


@dataclass(slots=True)
class EventCluster:
    cluster_key: str
    cluster_summary: str
    canonical_event_index: int
    event_indexes: list[int] = field(default_factory=list)
    confidence_score: float = 0.7
    first_seen_at: str = ""
    last_seen_at: str = ""


def cluster_events(events: list[StructuredEvent]) -> list[EventCluster]:
    buckets: dict[str, list[tuple[int, StructuredEvent]]] = {}
    for index, event in enumerate(events):
        cluster_key = _cluster_key(event)
        buckets.setdefault(cluster_key, []).append((index, event))

    clusters: list[EventCluster] = []
    for cluster_key, members in buckets.items():
        canonical_index, canonical_event = members[0]
        timestamps = [member.timestamp for _, member in members if member.timestamp]
        clusters.append(
            EventCluster(
                cluster_key=cluster_key,
                cluster_summary=canonical_event.summary,
                canonical_event_index=canonical_index,
                event_indexes=[index for index, _ in members],
                confidence_score=_confidence_score(members),
                first_seen_at=min(timestamps) if timestamps else "",
                last_seen_at=max(timestamps) if timestamps else "",
            )
        )
    return clusters


def _cluster_key(event: StructuredEvent) -> str:
    topic = _normalize_topic(event.summary)
    basis = "|".join(
        [
            event.person.strip().lower() or "unknown-person",
            event.event_type.strip().lower(),
            topic,
        ]
    )
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()


def _normalize_topic(summary: str) -> str:
    words = re.findall(r"[a-z0-9]+", summary.lower())
    if not words:
        return "generic"
    return "-".join(words[:6])


def _confidence_score(members: list[tuple[int, StructuredEvent]]) -> float:
    if len(members) >= 3:
        return 0.92
    if len(members) == 2:
        return 0.84
    return 0.72
