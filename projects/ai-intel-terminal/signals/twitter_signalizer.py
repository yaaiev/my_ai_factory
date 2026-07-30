"""
相对路径：projects/ai-intel-terminal/signals/twitter_signalizer.py
文件说明：将 Twitter/X 原始行为记录转成结构化投资信号。
"""
from __future__ import annotations

from connectors.x_signals import RawXSignal
from seeds.registry import SeedPerson


def classify_signal(raw_signal: RawXSignal) -> str:
    text = f"{raw_signal.content} {' '.join(raw_signal.tags or [])}".lower()
    if any(keyword in text for keyword in ("gpu", "cluster", "data center", "training", "deployment")):
        return "infra_expansion"
    if any(keyword in text for keyword in ("funding", "raise", "round", "investor", "valuation")):
        return "funding"
    if any(keyword in text for keyword in ("launch", "release", "rollout", "new model", "grok", "chatgpt", "claude")):
        return "model_release"
    if any(keyword in text for keyword in ("hiring", "joined", "safety engineer", "recruiting")):
        return "talent_move"
    if any(keyword in text for keyword in ("regulation", "policy", "hearing", "investigation")):
        return "policy"
    if any(keyword in text for keyword in ("agent", "multimodal", "video", "reasoning", "safety")):
        return "technical_discussion"
    if raw_signal.raw_type in {"retweet"}:
        return "noise"
    return "product_iteration"


def actor_weight(raw_signal: RawXSignal, seed_people: list[SeedPerson]) -> float:
    author = raw_signal.author.lower()
    for person in seed_people:
        if person.name.lower() == author:
            return 0.9
        if person.twitter_handle and person.twitter_handle.lower() == author.lstrip("@"):
            return 0.9
        if author in {alias.lower().lstrip("@") for alias in person.aliases}:
            return 0.85
    if raw_signal.observed_relationship == "first_degree_neighbor":
        return 0.58
    return 0.45
