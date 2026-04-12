"""
相对路径：projects/ai-intel-terminal/twitter_observer/contracts.py
文件说明：Twitter/X 浏览器观察层的数据结构。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class BrowserObserverConfig:
    base_url: str = "https://x.com"
    user_data_dir: str = ""
    cdp_url: str = ""
    browser_channel: str = "chrome"
    headless: bool = False
    observation_window_days: int = 30
    behavior_types: list[str] = field(default_factory=lambda: ["tweet_post", "reply", "retweet", "like"])
    neighbor_frequency_threshold: int = 2
    max_items_per_view: int = 10


@dataclass(slots=True)
class ObservedTweet:
    source: str
    author: str
    content: str
    timestamp: str
    raw_type: str
    source_url: str
    observed_via: str
    observed_relationship: str
    fetch_route: str = ""
    target_actor: str = ""
    metrics: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    seed_key: str = ""


@dataclass(slots=True)
class DiscoveredNeighbor:
    handle: str
    mention_count: int
    discovered_from: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SeedViewDiagnostic:
    seed_name: str
    handle: str
    view_name: str
    page_url: str = ""
    page_title: str = ""
    article_count: int = 0
    extracted_count: int = 0
    stale_candidate_count: int = 0
    missing_timestamp_count: int = 0
    missing_status_link_count: int = 0
    sample_timestamp: str = ""
    sample_status_url: str = ""
    sample_excerpt: str = ""
    sample_html: str = ""
    note: str = ""


@dataclass(slots=True)
class ObservationDiagnostics:
    dependency_ready: bool
    browser_ready: bool
    successful_seeds: list[str] = field(default_factory=list)
    failed_seeds: dict[str, str] = field(default_factory=dict)
    behavior_counts: dict[str, int] = field(default_factory=dict)
    route_counts: dict[str, int] = field(default_factory=dict)
    discovered_neighbors: list[DiscoveredNeighbor] = field(default_factory=list)
    seed_view_diagnostics: list[SeedViewDiagnostic] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
