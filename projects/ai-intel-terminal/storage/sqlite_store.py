"""
相对路径：projects/ai-intel-terminal/storage/sqlite_store.py
文件说明：MVP SQLite 落库工具，承接 raw_documents 和 events 的最小持久化。
"""
from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from connectors.contracts import RawDocument
from etl.contracts import StructuredEvent
from etl.clustering import EventCluster


class SQLiteStore:
    def __init__(self, db_path: Path, schema_path: Path):
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        schema_sql = self.schema_path.read_text(encoding="utf-8")
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema_sql)
            conn.commit()

    def upsert_source(
        self,
        source_name: str,
        source_type: str,
        base_url: str,
        signal_tier: str = "high",
        access_mode: str = "rss",
        notes: str = "",
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "select id from sources where source_name = ? and base_url = ?",
                (source_name, base_url),
            ).fetchone()
            if existing:
                return int(existing[0])

            cursor = conn.execute(
                """
                insert into sources (
                    source_type, source_name, base_url, signal_tier, access_mode, notes
                ) values (?, ?, ?, ?, ?, ?)
                """,
                (source_type, source_name, base_url, signal_tier, access_mode, notes),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def insert_raw_document(self, source_id: int, document: RawDocument) -> int:
        content_hash = hashlib.sha1(
            f"{document.url}|{document.title}|{document.raw_text}".encode("utf-8")
        ).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "select id from raw_documents where content_hash = ?",
                (content_hash,),
            ).fetchone()
            if existing:
                return int(existing[0])

            cursor = conn.execute(
                """
                insert into raw_documents (
                    source_id, external_id, url, author_name, published_at, title,
                    raw_text, language, ingested_at, content_hash
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    document.external_id,
                    document.url,
                    document.author_name,
                    document.published_at,
                    document.title,
                    document.raw_text,
                    document.language,
                    _utc_now(),
                    content_hash,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def insert_event(self, source_document_id: int, event: StructuredEvent) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                insert into events (
                    source_document_id, event_type, event_time, summary, sentiment,
                    risk_score, relevance_score, signal_strength, is_rumor, status, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_document_id,
                    event.event_type,
                    event.timestamp or _utc_now(),
                    event.summary,
                    event.sentiment,
                    event.risk_score,
                    event.relevance_score,
                    _signal_strength(event.signal_strength_score),
                    1 if event.event_type == "rumor" else 0,
                    "candidate",
                    _utc_now(),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def insert_event_cluster(self, cluster: EventCluster, canonical_event_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "select id from event_clusters where cluster_key = ?",
                (cluster.cluster_key,),
            ).fetchone()
            if existing:
                return int(existing[0])

            cursor = conn.execute(
                """
                insert into event_clusters (
                    cluster_key, canonical_event_id, cluster_summary, confidence_score,
                    first_seen_at, last_seen_at
                ) values (?, ?, ?, ?, ?, ?)
                """,
                (
                    cluster.cluster_key,
                    canonical_event_id,
                    cluster.cluster_summary,
                    cluster.confidence_score,
                    cluster.first_seen_at,
                    cluster.last_seen_at,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def insert_event_cluster_member(
        self,
        cluster_id: int,
        event_id: int,
        similarity_score: float,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                insert or replace into event_cluster_members (
                    cluster_id, event_id, similarity_score
                ) values (?, ?, ?)
                """,
                (cluster_id, event_id, similarity_score),
            )
            conn.commit()

    def summarize_counts(self) -> dict[str, int]:
        with sqlite3.connect(self.db_path) as conn:
            return {
                "sources": _count(conn, "sources"),
                "raw_documents": _count(conn, "raw_documents"),
                "events": _count(conn, "events"),
                "event_clusters": _count(conn, "event_clusters"),
                "event_cluster_members": _count(conn, "event_cluster_members"),
                "delivery_artifacts": _count(conn, "delivery_artifacts"),
            }

    def insert_delivery_artifact(
        self,
        artifact_type: str,
        artifact_date: str,
        title: str,
        body_markdown: str,
        source_scope: str,
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                insert into delivery_artifacts (
                    artifact_type, artifact_date, title, body_markdown, source_scope, created_at
                ) values (?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_type,
                    artifact_date,
                    title,
                    body_markdown,
                    source_scope,
                    _utc_now(),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)


def event_to_dict(event: StructuredEvent) -> dict[str, object]:
    return asdict(event)


def _count(conn: sqlite3.Connection, table_name: str) -> int:
    row = conn.execute(f"select count(*) from {table_name}").fetchone()
    return int(row[0]) if row else 0


def _signal_strength(signal_strength_score: float) -> str:
    if signal_strength_score >= 0.8:
        return "high"
    if signal_strength_score >= 0.5:
        return "medium"
    return "low"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
