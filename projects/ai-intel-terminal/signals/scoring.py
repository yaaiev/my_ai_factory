"""
相对路径：projects/ai-intel-terminal/signals/scoring.py
文件说明：Twitter/X 信号评分。
"""
from __future__ import annotations

import json
from pathlib import Path

from connectors.x_signals import RawXSignal
from seeds.registry import SeedPerson
from .contracts import ScoredSignal
from .twitter_signalizer import actor_weight, classify_signal


def score_signal(
    raw_signal: RawXSignal,
    seed_people: list[SeedPerson],
    taxonomy_path: Path,
    decision_rules_path: Path,
) -> ScoredSignal:
    signal_class = classify_signal(raw_signal)
    taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    behavior_weight = _behavior_weight(raw_signal.raw_type, taxonomy)
    actor_score = actor_weight(raw_signal, seed_people)
    propagation = _propagation_weight(raw_signal)
    consistency = _consistency_weight(raw_signal)
    signal_score = round(actor_score * behavior_weight * propagation * consistency, 4)
    impact, action = _decision_mapping(signal_class, raw_signal, decision_rules_path)
    risk_score = _risk_score(signal_class, raw_signal)
    return ScoredSignal(
        actor=raw_signal.author,
        signal_class=signal_class,
        behavior_type=raw_signal.raw_type,
        summary=raw_signal.content,
        source_link=raw_signal.url,
        timestamp=raw_signal.timestamp,
        signal_score=signal_score,
        actor_weight=actor_score,
        behavior_weight=behavior_weight,
        propagation_weight=propagation,
        consistency_weight=consistency,
        risk_score=risk_score,
        mapped_impact=impact,
        mapped_action=action,
        target_actor=raw_signal.referenced_actor,
        observed_via=raw_signal.observed_via,
        observed_relationship=raw_signal.observed_relationship,
        fetch_route=raw_signal.fetch_route,
        research_reason_zh=_research_reason(signal_class, raw_signal),
        score_breakdown={
            "actor_weight": actor_score,
            "behavior_weight": behavior_weight,
            "propagation_weight": propagation,
            "consistency_weight": consistency,
        },
        tags=list(raw_signal.tags or []),
    )


def _behavior_weight(raw_type: str, taxonomy: dict) -> float:
    for entry in taxonomy.get("behavior_types", []):
        if entry.get("key") == raw_type:
            return float(entry.get("weight", 0.3))
        if raw_type == "repost" and entry.get("key") == "retweet":
            return float(entry.get("weight", 0.3))
    return 0.3


def _propagation_weight(raw_signal: RawXSignal) -> float:
    metrics = raw_signal.metrics or {}
    likes = float(metrics.get("likes", 0))
    reposts = float(metrics.get("reposts", 0))
    replies = float(metrics.get("replies", 0))
    score = 0.55
    if likes >= 1000 or reposts >= 100:
        score = 0.95
    elif likes >= 200 or reposts >= 20 or replies >= 10:
        score = 0.8
    return score


def _consistency_weight(raw_signal: RawXSignal) -> float:
    tags = set(raw_signal.tags or [])
    if len(tags) >= 3:
        return 0.95
    if len(tags) == 2:
        return 0.85
    if len(tags) == 1:
        return 0.75
    return 0.6


def _decision_mapping(signal_class: str, raw_signal: RawXSignal, decision_rules_path: Path) -> tuple[str, str]:
    rules = json.loads(decision_rules_path.read_text(encoding="utf-8")).get("rules", [])
    text = f"{raw_signal.content} {' '.join(raw_signal.tags or [])}".lower()
    for rule in rules:
        if rule.get("signal_class") != signal_class:
            continue
        keywords = [keyword.lower() for keyword in rule.get("keywords", [])]
        if any(keyword in text for keyword in keywords):
            return rule.get("impact", ""), rule.get("action", "")
    return "需进一步结合其他源交叉验证。", "暂列为观察信号，等待更多一致性证据。"


def _risk_score(signal_class: str, raw_signal: RawXSignal) -> float:
    base = {
        "policy": 0.72,
        "funding": 0.55,
        "infra_expansion": 0.42,
        "talent_move": 0.46,
        "model_release": 0.4,
        "technical_discussion": 0.28,
        "product_iteration": 0.22,
        "noise": 0.1,
    }.get(signal_class, 0.2)
    if raw_signal.raw_type in {"reply", "silence_break"}:
        base += 0.05
    return round(min(base, 0.95), 4)


def _research_reason(signal_class: str, raw_signal: RawXSignal) -> str:
    reasons = {
        "infra_expansion": "该行为指向算力、部署或基础设施扩张，是 AI Infra 板块的前导观察信号。",
        "funding": "该行为涉及资金、估值或资本动作，通常会影响公司资源获取能力与市场预期。",
        "model_release": "该行为靠近模型或产品节奏，通常早于正式新闻成为市场关注点。",
        "talent_move": "该行为指向招聘或组织配置变化，常常领先于后续产品与战略动作。",
        "policy": "该行为与监管表态或政策边界有关，可能影响行业风险溢价。",
        "technical_discussion": "该行为反映技术主题升温，适合作为趋势温度计而不是单独交易依据。",
        "product_iteration": "该行为更偏产品迭代或开发者生态动态，需要与其他源交叉确认。",
        "noise": "该行为传播价值有限，应低权重处理。",
    }
    reason = reasons.get(signal_class, "该行为需要结合其他来源进一步解释。")
    if raw_signal.observed_relationship == "first_degree_neighbor":
        return f"{reason} 当前主体属于一度关系人物，因此权重低于核心 seed。"
    return reason
