"""
相对路径：projects/ai-intel-terminal/etl/dedup.py
文件说明：MVP 去重模块，提供文档级与事件级轻量去重。
"""
from __future__ import annotations

import hashlib

from connectors.contracts import RawDocument
from etl.contracts import StructuredEvent


def dedupe_documents(documents: list[RawDocument]) -> list[RawDocument]:
    seen: set[str] = set()
    unique_documents: list[RawDocument] = []
    for document in documents:
        fingerprint = _document_fingerprint(document)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique_documents.append(document)
    return unique_documents


def dedupe_events(events: list[StructuredEvent]) -> list[StructuredEvent]:
    seen: set[str] = set()
    unique_events: list[StructuredEvent] = []
    for event in events:
        fingerprint = _event_fingerprint(event)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique_events.append(event)
    return unique_events


def _document_fingerprint(document: RawDocument) -> str:
    normalized = f"{document.url.strip().lower()}|{document.title.strip().lower()}"
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def _event_fingerprint(event: StructuredEvent) -> str:
    normalized = (
        f"{event.link.strip().lower()}|{event.event_type}|"
        f"{event.summary.strip().lower()}|{event.person.strip().lower()}"
    )
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()
