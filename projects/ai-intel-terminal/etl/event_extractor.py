"""
相对路径：projects/ai-intel-terminal/etl/event_extractor.py
文件说明：第一阶段事件抽取器，占位实现基于规则的最小映射。
"""
from __future__ import annotations

import re

from .contracts import StructuredEvent
from connectors.contracts import RawDocument


KEYWORD_TO_EVENT_TYPE = {
    "funding": "funding_round",
    "raised": "funding_round",
    "partnership": "partnership",
    "partnered": "partnership",
    "launch": "model_release",
    "released": "model_release",
    "hiring": "talent_movement",
    "joined": "talent_movement",
    "policy": "policy_statement",
}

KEYWORD_PRIORITY_RULES = [
    (("responds to", "responded to", "backlash", "article", "attack on his home", "sues", "lawsuit"), "personal_incident"),
    (("banned", "suspended access", "controversy", "criticism"), "media_reputation"),
    (("launch", "released", "release notes", "rollout", "native app", "pro plan"), "model_release"),
    (("hiring", "joins", "joined", "recruiting", "expands hiring"), "talent_movement"),
    (("policy", "regulation", "regulatory", "hearing"), "policy_statement"),
    (("funding", "raised", "investing billions", "acquisition"), "funding_round"),
    (("partnership", "partnered", "collaboration"), "partnership"),
    (("gpu", "deployment capacity", "cluster", "data center", "infrastructure"), "infra_expansion"),
]

ORG_KEYWORDS = [
    "OpenAI",
    "Anthropic",
    "Microsoft",
    "Meta",
    "Google",
    "Google DeepMind",
    "DeepMind",
    "NVIDIA",
    "Amazon",
    "AWS",
    "Intel",
    "xAI",
    "ChatGPT",
    "Claude",
    "Gemini",
]


def extract_event(document: RawDocument) -> StructuredEvent:
    text = f"{document.title}\n{document.raw_text}".lower()
    event_type = infer_event_type(text, platform=document.source_key)
    entities = extract_entities(document)
    return StructuredEvent(
        person="",
        platform=document.source_key,
        timestamp=document.published_at,
        event_type=event_type,
        summary=document.title,
        sentiment="neutral",
        risk_score=0.0,
        relevance_score=0.5,
        link=document.url,
        raw_text=document.raw_text,
        signal_strength_score=infer_signal_strength_score(event_type),
        research_priority=infer_research_priority(event_type),
        entities=entities,
        matched_person_keys=[],
    )


def infer_event_type(text: str, platform: str = "") -> str:
    if platform == "github_org_activity":
        return infer_github_event_type(text)
    for keywords, event_type in KEYWORD_PRIORITY_RULES:
        if any(keyword in text for keyword in keywords):
            return event_type
    for keyword, event_type in KEYWORD_TO_EVENT_TYPE.items():
        if keyword in text:
            return event_type
    return "research_breakthrough"


def infer_github_event_type(text: str) -> str:
    if any(keyword in text for keyword in ("release:", "releases", "release ", "version", "rollout")):
        return "product_iteration"
    if any(keyword in text for keyword in ("feat(", "feat:", "support ", "api", "sdk", "client", "websocket")):
        return "product_iteration"
    if any(keyword in text for keyword in ("gpu", "cluster", "deployment", "inference", "trt", "tensorrt")):
        return "infra_expansion"
    if any(keyword in text for keyword in ("fix(", "fix:", "bugfix", "patch")):
        return "product_iteration"
    return "research_breakthrough"


def extract_entities(document: RawDocument) -> list[str]:
    haystack = f"{document.title}\n{document.raw_text}"
    entities: list[str] = []
    for org in ORG_KEYWORDS:
        pattern = rf"(^|\W){re.escape(org)}(\W|$)"
        if re.search(pattern, haystack, flags=re.IGNORECASE) and org not in entities:
            entities.append(org)
    return entities


def infer_signal_strength_score(event_type: str) -> float:
    weights = {
        "model_release": 0.85,
        "funding_round": 0.85,
        "infra_expansion": 0.8,
        "talent_movement": 0.72,
        "policy_statement": 0.7,
        "partnership": 0.68,
        "research_breakthrough": 0.62,
        "media_reputation": 0.48,
        "personal_incident": 0.45,
        "rumor": 0.38,
    }
    return weights.get(event_type, 0.5)


def infer_research_priority(event_type: str) -> str:
    if event_type in {"model_release", "funding_round", "infra_expansion"}:
        return "high"
    if event_type in {"talent_movement", "policy_statement", "partnership"}:
        return "medium"
    return "low"
