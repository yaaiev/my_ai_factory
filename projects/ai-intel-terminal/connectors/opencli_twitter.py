"""
相对路径：projects/ai-intel-terminal/connectors/opencli_twitter.py
文件说明：基于 OpenCLI 的 Twitter/X 真实数据 connector。
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from connectors.contracts import ConnectorHealth
from connectors.x_signals import RawXSignal
from seeds.registry import SeedPerson


@dataclass(slots=True)
class OpenCLITwitterProfile:
    screen_name: str
    name: str
    bio: str
    location: str
    url: str
    followers: int
    following: int
    tweets: int
    likes: int
    verified: bool
    created_at: str


class OpenCLITwitterConnector:
    source_key = "x_people_watch_opencli"

    def __init__(self, binary: str = "opencli"):
        self.binary = binary

    def healthcheck(self) -> ConnectorHealth:
        try:
            result = subprocess.run(
                [self.binary, "doctor"],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except FileNotFoundError:
            return ConnectorHealth.unhealthy(self.source_key, "未找到 opencli 可执行文件。")
        except subprocess.TimeoutExpired:
            return ConnectorHealth.unhealthy(self.source_key, "opencli doctor 超时。")

        output = f"{result.stdout}\n{result.stderr}".strip()
        if "[OK] Daemon" in output and "[OK] Extension" in output:
            return ConnectorHealth.healthy(self.source_key, "opencli daemon 与扩展均已连接。")
        return ConnectorHealth.unhealthy(self.source_key, output or "opencli doctor 未返回可用结果。")

    def fetch_profile(self, handle: str) -> OpenCLITwitterProfile | None:
        payload = self._run_json(["twitter", "profile", handle, "-f", "json"])
        if not payload:
            return None
        item = payload[0]
        return OpenCLITwitterProfile(
            screen_name=item.get("screen_name", handle),
            name=item.get("name", handle),
            bio=item.get("bio", ""),
            location=item.get("location", ""),
            url=item.get("url", ""),
            followers=_to_int(item.get("followers", 0)),
            following=_to_int(item.get("following", 0)),
            tweets=_to_int(item.get("tweets", 0)),
            likes=_to_int(item.get("likes", 0)),
            verified=bool(item.get("verified", False)),
            created_at=item.get("created_at", ""),
        )

    def fetch_recent_posts(
        self,
        seed: SeedPerson,
        since_days: int,
        limit: int = 10,
    ) -> list[RawXSignal]:
        handle = seed.twitter_handle.strip().lstrip("@")
        if not handle:
            return []
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).date().isoformat()
        query = f"from:{handle} since:{since}"
        payload = self._run_json(
            [
                "twitter",
                "search",
                query,
                "--filter",
                "live",
                "--limit",
                str(limit),
                "-f",
                "json",
            ]
        )
        signals: list[RawXSignal] = []
        for item in payload:
            text = (item.get("text") or "").strip()
            if not text:
                continue
            tags = infer_opencli_tags(text, seed)
            signals.append(
                RawXSignal(
                    source="twitter",
                    author=seed.name,
                    content=text,
                    timestamp=_normalize_created_at(item.get("created_at", "")),
                    raw_type=_infer_raw_type(text),
                    referenced_actor=_first_mentioned_actor(text),
                    url=item.get("url", ""),
                    source_url=item.get("url", ""),
                    observed_via="opencli",
                    observed_relationship="seed",
                    fetch_route="opencli_search_live",
                    seed_key=seed.key,
                    metrics={
                        "likes": _to_float(item.get("likes", 0)),
                        "views": _to_float(item.get("views", 0)),
                    },
                    tags=tags,
                )
            )
        return signals

    def _run_json(self, args: list[str]) -> list[dict[str, object]]:
        result = subprocess.run(
            [self.binary, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=45,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise RuntimeError(detail or f"opencli {' '.join(args)} failed")
        output = _extract_json_payload(result.stdout)
        if not output:
            return []
        parsed = json.loads(output)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
        return []


def infer_opencli_tags(text: str, seed: SeedPerson) -> list[str]:
    haystack = text.lower()
    tags: list[str] = []
    for keyword in seed.keywords:
        if keyword.lower() in haystack and keyword not in tags:
            tags.append(keyword)
    generic = ["codex", "chatgpt", "gpt", "claude", "grok", "gpu", "cluster", "launch", "release", "pro"]
    for keyword in generic:
        if keyword in haystack and keyword not in tags:
            tags.append(keyword)
    return tags[:6]


def _extract_json_payload(stdout: str) -> str:
    lines = stdout.splitlines()
    collected: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not started and stripped.startswith(("[", "{")):
            started = True
        if started:
            if stripped.startswith("Update available:") or stripped.startswith("Run: npm install"):
                break
            collected.append(line)
    return "\n".join(collected).strip()


def _normalize_created_at(value: str) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y").isoformat()
    except ValueError:
        return value


def _infer_raw_type(text: str) -> str:
    return "reply" if text.lstrip().startswith("@") else "tweet_post"


def _first_mentioned_actor(text: str) -> str:
    import re

    match = re.search(r"@([A-Za-z0-9_]{2,})", text)
    return f"@{match.group(1)}" if match else ""


def _to_int(value: object) -> int:
    try:
        return int(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0


def _to_float(value: object) -> float:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0
