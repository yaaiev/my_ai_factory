"""
相对路径：projects/ai-intel-terminal/etl/person_matcher.py
文件说明：基于 seed registry 的人物匹配器。
"""
from __future__ import annotations

import re

from connectors.contracts import RawDocument
from seeds.registry import SeedPerson


def match_people(document: RawDocument, seed_people: list[SeedPerson]) -> list[SeedPerson]:
    haystack = _normalize_text(
        " ".join(
            [
                document.title,
                document.raw_text,
                document.author_name,
                document.metadata.get("feed_url", ""),
            ]
        )
    )
    matches: list[SeedPerson] = []
    for person in seed_people:
        candidates = [person.name, *person.aliases]
        if person.twitter_handle:
            candidates.append(f"@{person.twitter_handle}")
            candidates.append(person.twitter_handle)
        if any(_contains_candidate(haystack, candidate) for candidate in candidates if candidate):
            matches.append(person)
    return matches


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _contains_candidate(haystack: str, candidate: str) -> bool:
    normalized = _normalize_text(candidate)
    if not normalized:
        return False
    if normalized.startswith("@"):
        return normalized in haystack
    pattern = rf"(^|\W){re.escape(normalized)}(\W|$)"
    return re.search(pattern, haystack) is not None
