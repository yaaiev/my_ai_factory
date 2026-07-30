"""
相对路径：projects/ai-intel-terminal/sources/catalog.py
文件说明：source catalog 读取与查询工具。
"""
from __future__ import annotations

import json
from pathlib import Path


def load_source_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_source_entry(path: Path, source_key: str) -> dict:
    catalog = load_source_catalog(path)
    for entry in catalog.get("sources", []):
        if entry.get("key") == source_key:
            return entry
    raise KeyError(f"source not found: {source_key}")
