"""
相对路径：projects/ai-intel-terminal/etl/contracts.py
文件说明：ETL 层统一事件结构。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class StructuredEvent:
    person: str
    platform: str
    timestamp: str
    event_type: str
    summary: str
    sentiment: str
    risk_score: float
    relevance_score: float
    link: str
    raw_text: str
    signal_strength_score: float = 0.4
    research_priority: str = "medium"
    entities: list[str] = field(default_factory=list)
    matched_person_keys: list[str] = field(default_factory=list)
