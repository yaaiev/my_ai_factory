"""
相对路径：projects/ai-intel-terminal/connectors/rss_news.py
文件说明：RSS/News connector MVP，用于打通第一条 raw_document 链路。
"""
from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from dataclasses import asdict
from urllib.request import Request, urlopen

from .contracts import ConnectorHealth, RawDocument


class RSSNewsConnector:
    source_key = "ai_news_rss"

    def __init__(self, urls: list[str], timeout_seconds: int = 20):
        self.urls = urls
        self.timeout_seconds = timeout_seconds

    def fetch_raw(self) -> list[RawDocument]:
        documents: list[RawDocument] = []
        for url in self.urls:
            xml_text = self._fetch_xml(url)
            if not xml_text:
                continue
            documents.extend(self._parse_feed(xml_text, url))
        return documents

    def healthcheck(self) -> ConnectorHealth:
        if not self.urls:
            return ConnectorHealth.unhealthy(self.source_key, "no feed urls configured")
        try:
            self._fetch_xml(self.urls[0])
        except Exception as exc:
            return ConnectorHealth.unhealthy(self.source_key, str(exc))
        return ConnectorHealth.healthy(self.source_key, "rss feed reachable")

    def _fetch_xml(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": "ai-intel-terminal/0.1 (+https://github.com/yaaiev/my_ai_factory)",
            },
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")

    def _parse_feed(self, xml_text: str, fallback_url: str) -> list[RawDocument]:
        root = ET.fromstring(xml_text)
        items = root.findall(".//item")
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        documents = [self._parse_rss_item(item, fallback_url) for item in items]
        documents.extend(self._parse_atom_entry(entry, fallback_url) for entry in entries)

        return [doc for doc in documents if doc is not None]

    def _parse_rss_item(self, item: ET.Element, fallback_url: str) -> RawDocument | None:
        title = _text_or(item.find("title"), "Untitled feed item")
        link = _text_or(item.find("link"), fallback_url)
        published_at = _text_or(item.find("pubDate"), "")
        description = _text_or(item.find("description"), "")
        author = _text_or(item.find("author"), "")
        external_id = _stable_id(link, title)
        return RawDocument(
            source_key=self.source_key,
            external_id=external_id,
            url=link,
            title=title,
            author_name=author,
            published_at=published_at,
            raw_text=description or title,
            metadata={"feed_url": fallback_url},
        )

    def _parse_atom_entry(self, entry: ET.Element, fallback_url: str) -> RawDocument | None:
        ns = "{http://www.w3.org/2005/Atom}"
        title = _text_or(entry.find(f"{ns}title"), "Untitled atom entry")
        updated = _text_or(entry.find(f"{ns}updated"), "")
        summary = _text_or(entry.find(f"{ns}summary"), "")
        author = _text_or(entry.find(f"{ns}author/{ns}name"), "")
        link_elem = entry.find(f"{ns}link")
        link = link_elem.attrib.get("href", fallback_url) if link_elem is not None else fallback_url
        external_id = _stable_id(link, title)
        return RawDocument(
            source_key=self.source_key,
            external_id=external_id,
            url=link,
            title=title,
            author_name=author,
            published_at=updated,
            raw_text=summary or title,
            metadata={"feed_url": fallback_url},
        )


def serialize_documents(documents: list[RawDocument]) -> list[dict[str, object]]:
    return [asdict(doc) for doc in documents]


def _stable_id(link: str, title: str) -> str:
    return hashlib.sha1(f"{link}|{title}".encode("utf-8")).hexdigest()


def _text_or(element: ET.Element | None, default: str) -> str:
    if element is None or element.text is None:
        return default
    return element.text.strip() or default
