"""
相对路径：projects/ai-intel-terminal/connectors/contracts.py
文件说明：采集 connector 的统一协议与核心数据结构。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


@dataclass(slots=True)
class RawDocument:
    source_key: str
    external_id: str
    url: str
    title: str
    author_name: str
    published_at: str
    raw_text: str
    language: str = "en"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ConnectorHealth:
    source_key: str
    ok: bool
    checked_at: str
    detail: str = ""

    @classmethod
    def healthy(cls, source_key: str, detail: str = "") -> "ConnectorHealth":
        return cls(
            source_key=source_key,
            ok=True,
            checked_at=datetime.now(timezone.utc).isoformat(),
            detail=detail,
        )

    @classmethod
    def unhealthy(cls, source_key: str, detail: str) -> "ConnectorHealth":
        return cls(
            source_key=source_key,
            ok=False,
            checked_at=datetime.now(timezone.utc).isoformat(),
            detail=detail,
        )


class BaseConnector(Protocol):
    source_key: str

    def fetch_raw(self) -> list[RawDocument]:
        """Fetch raw documents from the source."""

    def healthcheck(self) -> ConnectorHealth:
        """Return source health and minimal diagnostics."""
