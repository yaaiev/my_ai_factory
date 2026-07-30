"""
相对路径：projects/ai-intel-terminal/connectors/github_activity.py
文件说明：GitHub 活动 connector 基础骨架，基于公开 atom feed。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

from .contracts import ConnectorHealth, RawDocument


class GitHubActivityConnector:
    source_key = "github_org_activity"

    def __init__(self, feed_urls: list[str], timeout_seconds: int = 20):
        self.feed_urls = feed_urls
        self.timeout_seconds = timeout_seconds

    def fetch_raw(self) -> list[RawDocument]:
        documents, _ = self.fetch_raw_with_diagnostics()
        return documents

    def fetch_raw_with_diagnostics(self) -> tuple[list[RawDocument], list[dict[str, object]]]:
        documents: list[RawDocument] = []
        diagnostics: list[dict[str, object]] = []
        for feed_url in self.feed_urls:
            try:
                xml_text = self._fetch_xml(feed_url)
                feed_documents = self._parse_atom(xml_text, feed_url)
                documents.extend(feed_documents)
                diagnostics.append(
                    {
                        "feed_url": feed_url,
                        "ok": True,
                        "document_count": len(feed_documents),
                        "error": "",
                    }
                )
            except Exception as exc:
                diagnostics.append(
                    {
                        "feed_url": feed_url,
                        "ok": False,
                        "document_count": 0,
                        "error": str(exc),
                    }
                )
        return documents, diagnostics

    def healthcheck(self) -> ConnectorHealth:
        if not self.feed_urls:
            return ConnectorHealth.unhealthy(self.source_key, "no github feeds configured")
        try:
            self._fetch_xml(self.feed_urls[0])
        except Exception as exc:
            return ConnectorHealth.unhealthy(self.source_key, str(exc))
        return ConnectorHealth.healthy(self.source_key, "github atom feed reachable")

    def _fetch_xml(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": "ai-intel-terminal/0.1 (+https://github.com/yaaiev/my_ai_factory)",
            },
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")

    def _parse_atom(self, xml_text: str, feed_url: str) -> list[RawDocument]:
        ns = "{http://www.w3.org/2005/Atom}"
        root = ET.fromstring(xml_text)
        documents: list[RawDocument] = []
        for entry in root.findall(f".//{ns}entry"):
            title = _text_or(entry.find(f"{ns}title"), "Untitled GitHub event")
            updated = _text_or(entry.find(f"{ns}updated"), "")
            author = _text_or(entry.find(f"{ns}author/{ns}name"), "")
            summary = _text_or(entry.find(f"{ns}content"), title)
            link_elem = entry.find(f"{ns}link")
            link = link_elem.attrib.get("href", feed_url) if link_elem is not None else feed_url
            entry_id = _text_or(entry.find(f"{ns}id"), link)
            documents.append(
                RawDocument(
                    source_key=self.source_key,
                    external_id=entry_id,
                    url=link,
                    title=title,
                    author_name=author,
                    published_at=updated,
                    raw_text=summary,
                    metadata={"feed_url": feed_url},
                )
            )
        return documents


def _text_or(element: ET.Element | None, default: str) -> str:
    if element is None or element.text is None:
        return default
    return element.text.strip() or default
