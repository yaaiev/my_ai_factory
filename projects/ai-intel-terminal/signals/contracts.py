"""
相对路径：projects/ai-intel-terminal/signals/contracts.py
文件说明：Twitter/X 投资信号结构定义。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ScoredSignal:
    actor: str
    signal_class: str
    behavior_type: str
    summary: str
    source_link: str
    timestamp: str
    signal_score: float
    actor_weight: float
    behavior_weight: float
    propagation_weight: float
    consistency_weight: float
    risk_score: float
    mapped_impact: str
    mapped_action: str
    target_actor: str = ""
    observed_via: str = ""
    observed_relationship: str = "seed"
    fetch_route: str = ""
    research_reason_zh: str = ""
    score_breakdown: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
