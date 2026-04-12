"""
相对路径：projects/ai-intel-terminal/seeds/registry.py
文件说明：人物 seed 注册表加载与查询。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class SeedPerson:
    key: str
    name: str
    aliases: list[str] = field(default_factory=list)
    current_company: str = ""
    title: str = ""
    category: str = ""
    twitter_handle: str = ""
    github_login: str = ""
    keywords: list[str] = field(default_factory=list)
    source_preferences: list[str] = field(default_factory=list)
    risk_vector: list[str] = field(default_factory=list)
    related_people: list[str] = field(default_factory=list)


def load_seed_people(path: Path) -> list[SeedPerson]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    people = []
    for entry in raw.get("persons", []):
        people.append(
            SeedPerson(
                key=entry["key"],
                name=entry["name"],
                aliases=list(entry.get("aliases", [])),
                current_company=entry.get("current_company", ""),
                title=entry.get("title", ""),
                category=entry.get("category", ""),
                twitter_handle=entry.get("twitter_handle", ""),
                github_login=entry.get("github_login", ""),
                keywords=list(entry.get("keywords", [])),
                source_preferences=list(entry.get("source_preferences", [])),
                risk_vector=list(entry.get("risk_vector", [])),
                related_people=list(entry.get("related_people", [])),
            )
        )
    return people
