"""
相对路径：projects/ai-intel-terminal/pipelines/common.py
文件说明：单源/多源 pipeline 的共享处理逻辑。
"""
from __future__ import annotations

from pathlib import Path

from connectors.contracts import RawDocument
from delivery.daily_brief import build_daily_brief
from etl.clustering import EventCluster, cluster_events
from etl.contracts import StructuredEvent
from etl.dedup import dedupe_documents
from etl.event_extractor import extract_event
from etl.person_matcher import match_people
from seeds.registry import SeedPerson
from storage.sqlite_store import SQLiteStore


def prepare_events(
    documents: list[RawDocument],
    seed_people: list[SeedPerson],
) -> list[tuple[RawDocument, StructuredEvent]]:
    event_records: list[tuple[RawDocument, StructuredEvent]] = []
    for document in dedupe_documents(documents):
        event = extract_event(document)
        matches = match_people(document, seed_people)
        if matches:
            event.person = matches[0].name
            event.matched_person_keys = [person.key for person in matches]
            event.entities = [person.current_company for person in matches if person.current_company]
            event.relevance_score = 0.85
            event.signal_strength_score = min(1.0, event.signal_strength_score + 0.1)
            if event.research_priority == "low":
                event.research_priority = "medium"
        event_records.append((document, event))
    return dedupe_event_records(event_records)


def persist_source_run(
    store: SQLiteStore,
    source_id: int,
    event_records: list[tuple[RawDocument, StructuredEvent]],
) -> list[dict[str, object]]:
    persisted_records: list[dict[str, object]] = []
    for document, event in event_records:
        raw_document_id = store.insert_raw_document(source_id=source_id, document=document)
        event_id = store.insert_event(source_document_id=raw_document_id, event=event)
        persisted_records.append(
            {
                "raw_document_id": raw_document_id,
                "event_id": event_id,
                "document": document,
                "event": event,
            }
        )
    return persisted_records


def persist_clusters(
    store: SQLiteStore,
    persisted_records: list[dict[str, object]],
) -> list[dict[str, object]]:
    events = [record["event"] for record in persisted_records]
    clusters = cluster_events(events)
    cluster_rows: list[dict[str, object]] = []
    for cluster in clusters:
        canonical_event_id = persisted_records[cluster.canonical_event_index]["event_id"]
        cluster_id = store.insert_event_cluster(cluster, canonical_event_id=canonical_event_id)
        member_ids = []
        for event_index in cluster.event_indexes:
            event_id = persisted_records[event_index]["event_id"]
            store.insert_event_cluster_member(
                cluster_id=cluster_id,
                event_id=event_id,
                similarity_score=cluster.confidence_score,
            )
            member_ids.append(event_id)
        cluster_rows.append(
            {
                "cluster_id": cluster_id,
                "cluster_key": cluster.cluster_key,
                "cluster_summary": cluster.cluster_summary,
                "member_event_ids": member_ids,
                "confidence_score": cluster.confidence_score,
            }
        )
    return cluster_rows


def write_daily_brief_artifact(
    store: SQLiteStore,
    artifact_date: str,
    title: str,
    source_scope: str,
    events: list[StructuredEvent],
    clusters: list[EventCluster],
    output_path: Path,
    language: str = "zh",
    report_mode: str = "formal",
) -> str:
    markdown = build_daily_brief(
        events=events,
        clusters=clusters,
        title=title,
        language=language,
        report_mode=report_mode,
    )
    output_path.write_text(markdown, encoding="utf-8")
    store.insert_delivery_artifact(
        artifact_type=f"daily_brief_{language}_{report_mode}",
        artifact_date=artifact_date,
        title=title,
        body_markdown=markdown,
        source_scope=source_scope,
    )
    return markdown


def dedupe_event_records(
    records: list[tuple[RawDocument, StructuredEvent]],
) -> list[tuple[RawDocument, StructuredEvent]]:
    kept: list[tuple[RawDocument, StructuredEvent]] = []
    seen: set[str] = set()
    for document, event in records:
        fingerprint = event_fingerprint(event)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        kept.append((document, event))
    return kept


def event_fingerprint(event: StructuredEvent) -> str:
    from etl.dedup import _event_fingerprint

    return _event_fingerprint(event)
