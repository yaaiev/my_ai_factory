"""
相对路径：projects/ai-intel-terminal/twitter_observer/extractor.py
文件说明：Twitter/X 页面 article 提取与路由级诊断工具。
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

from seeds.registry import SeedPerson


def extract_article_payloads(page, limit: int) -> list[dict[str, object]]:
    return page.evaluate(
        """
        (limit) => {
          const articles = Array.from(document.querySelectorAll('article')).slice(0, limit);
          return articles.map((article) => {
            const timeEl = article.querySelector('time');
            const links = Array.from(article.querySelectorAll('a')).map((a) => a.href || '');
            const linkEl = Array.from(article.querySelectorAll('a')).find((a) => a.href && a.href.includes('/status/'));
            const textEls = Array.from(article.querySelectorAll('[data-testid="tweetText"]'));
            const text = textEls.length
              ? textEls.map((el) => el.innerText || '').join('\\n').trim()
              : (article.innerText || '').trim();
            const metrics = {};
            for (const key of ['reply', 'retweet', 'like', 'view']) {
              const node = article.querySelector(`[data-testid="${key}"]`);
              if (!node) continue;
              const raw = (node.innerText || '').replace(/,/g, '');
              const value = Number(raw) || 0;
              metrics[key + 's'] = value;
            }
            return {
              content: text,
              timestamp: timeEl ? timeEl.getAttribute('datetime') || '' : '',
              source_url: linkEl ? linkEl.href : '',
              link_candidates: links.filter(Boolean).slice(0, 8),
              html: (article.outerHTML || '').slice(0, 4000),
              metrics,
            };
          });
        }
        """,
        limit,
    )


def first_status_link(candidates: list[str]) -> str:
    for candidate in candidates:
        if "/status/" in candidate:
            return candidate
    return ""


def parse_datetime(value: str) -> datetime | None:
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def fallback_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def first_mentioned_actor(text: str) -> str:
    import re

    match = re.search(r"@([A-Za-z0-9_]{2,})", text)
    return f"@{match.group(1)}" if match else ""


def infer_target_actor(text: str, source_url: str, seed_handle: str) -> str:
    mentioned = first_mentioned_actor(text)
    if mentioned:
        return mentioned
    parsed = urlparse(source_url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[1] == "status":
        author_handle = f"@{parts[0]}"
        if author_handle.lower().lstrip("@") != seed_handle.lower():
            return author_handle
    return ""


def infer_tags(text: str, seed: SeedPerson) -> list[str]:
    haystack = text.lower()
    tags: list[str] = []
    for keyword in seed.keywords:
        keyword_norm = keyword.lower()
        if keyword_norm in haystack and keyword not in tags:
            tags.append(keyword)
    generic_tags = [
        "gpu",
        "cluster",
        "data center",
        "agent",
        "reasoning",
        "safety",
        "hiring",
        "release",
        "launch",
        "policy",
    ]
    for keyword in generic_tags:
        if keyword in haystack and keyword not in tags:
            tags.append(keyword)
    return tags[:6]


def infer_page_note(
    page_title: str,
    page_url: str,
    requested_url: str,
    article_count: int,
    extracted_count: int,
    stale_candidate_count: int,
    missing_timestamp_count: int,
    missing_status_link_count: int,
    is_search_fallback: bool,
) -> str:
    title = page_title.lower()
    current = page_url.lower()
    if "i/flow/login" in current:
        return "页面跳转到登录流程。"
    if requested_url.endswith("/likes") and current.rstrip("/") == requested_url.rsplit("/", 1)[0].lower():
        return "likes 视图被重定向回主页，当前登录态可能无权访问该账号点赞页。"
    if "something went wrong" in title:
        return "页面返回错误页。"
    if article_count == 0:
        if is_search_fallback:
            return "recent search 视图未检测到 article 元素。"
        return "页面未检测到 article 元素。"
    if extracted_count == 0:
        if stale_candidate_count and stale_candidate_count >= article_count:
            if is_search_fallback:
                return "recent search 视图存在 article，但当前可见卡片均早于时间窗口。"
            return "检测到 article，但当前可见卡片均早于时间窗口。"
        if missing_timestamp_count and not missing_status_link_count:
            return "检测到 article，但多数卡片缺少可解析时间戳。"
        if missing_status_link_count and not missing_timestamp_count:
            return "检测到 article，但多数卡片缺少可解析状态链接。"
        if missing_status_link_count and missing_timestamp_count:
            return "检测到 article，但卡片同时缺少时间戳和状态链接。"
        return "检测到 article，但未提取出满足时间窗口和链接条件的内容。"
    return ""
