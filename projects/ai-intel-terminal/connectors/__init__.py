"""Connector package for AI Intel Terminal MVP."""

from .contracts import RawDocument, ConnectorHealth, BaseConnector
from .github_activity import GitHubActivityConnector
from .rss_news import RSSNewsConnector

__all__ = [
    "BaseConnector",
    "ConnectorHealth",
    "GitHubActivityConnector",
    "RawDocument",
    "RSSNewsConnector",
]
