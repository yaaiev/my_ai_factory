"""
相对路径：projects/ai-intel-terminal/twitter_observer/browser_observer.py
文件说明：基于浏览器会话的 Twitter/X 观察层。优先复用已登录浏览器态。
"""
from __future__ import annotations

import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from connectors.contracts import ConnectorHealth
from seeds.registry import SeedPerson
from .adapters import build_route_adapters
from .contracts import (
    BrowserObserverConfig,
    DiscoveredNeighbor,
    ObservationDiagnostics,
    ObservedTweet,
    SeedViewDiagnostic,
)
from .extractor import (
    extract_article_payloads,
    fallback_timestamp,
    first_status_link,
    infer_page_note,
    infer_tags,
    infer_target_actor,
    parse_datetime,
)


class TwitterBrowserObserver:
    source_key = "x_people_watch"

    def __init__(self, config: BrowserObserverConfig):
        self.config = config

    def healthcheck(self) -> ConnectorHealth:
        playwright = _load_playwright()
        if playwright is None:
            return ConnectorHealth.unhealthy(
                self.source_key,
                "python 环境缺少 playwright，请先安装 playwright 并执行 `playwright install chromium`。",
            )
        if self.config.cdp_url:
            return ConnectorHealth.healthy(self.source_key, f"browser observer will connect over CDP: {self.config.cdp_url}")
        if not self.config.user_data_dir:
            return ConnectorHealth.unhealthy(
                self.source_key,
                "缺少浏览器连接信息。请设置 X_BROWSER_USER_DATA_DIR，或设置 X_BROWSER_CDP_URL 连接已打开的 Chrome。",
            )
        if not os.path.exists(self.config.user_data_dir):
            return ConnectorHealth.unhealthy(
                self.source_key,
                f"浏览器用户数据目录不存在：{self.config.user_data_dir}",
            )
        return ConnectorHealth.healthy(self.source_key, "browser observer prerequisites look ready")

    def observe(self, seed_people: list[SeedPerson]) -> tuple[list[ObservedTweet], ObservationDiagnostics]:
        browser_ready = bool(self.config.cdp_url) or bool(
            self.config.user_data_dir and os.path.exists(self.config.user_data_dir)
        )
        diagnostics = ObservationDiagnostics(
            dependency_ready=_load_playwright() is not None,
            browser_ready=browser_ready,
            behavior_counts={behavior_type: 0 for behavior_type in self.config.behavior_types},
            route_counts={adapter.route_key: 0 for adapter in build_route_adapters()},
        )
        if not diagnostics.dependency_ready:
            diagnostics.notes.append(
                "未检测到 playwright；当前仅完成代码层实现，真实抓取需要先安装浏览器自动化依赖。"
            )
            return [], diagnostics
        if not diagnostics.browser_ready:
            diagnostics.notes.append(
                "未检测到可复用的浏览器连接方式。当前默认优先使用 X_BROWSER_CDP_URL；若未提供 CDP，再退回 X_BROWSER_USER_DATA_DIR。"
            )
            return [], diagnostics

        sync_playwright = _load_playwright()
        records: list[ObservedTweet] = []
        neighbor_counts: Counter[str] = Counter()
        neighbor_sources: dict[str, set[str]] = defaultdict(set)
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.config.observation_window_days)
        with sync_playwright() as playwright:
            browser_or_context, page_factory, close_browser = self._open_browser(playwright, diagnostics)
            if browser_or_context is None:
                return [], diagnostics
            try:
                for seed in seed_people:
                    handle = seed.twitter_handle.strip().lstrip("@")
                    if not handle:
                        diagnostics.failed_seeds[seed.name] = "seed missing twitter_handle"
                        continue
                    try:
                        page = page_factory()
                        seed_records, seed_view_diagnostics = self._observe_seed(page, seed, cutoff)
                        page.close()
                        diagnostics.seed_view_diagnostics.extend(seed_view_diagnostics)
                        records.extend(seed_records)
                        if seed_records:
                            diagnostics.successful_seeds.append(seed.name)
                        for row in seed_records:
                            diagnostics.behavior_counts[row.raw_type] = diagnostics.behavior_counts.get(row.raw_type, 0) + 1
                            diagnostics.route_counts[row.fetch_route] = diagnostics.route_counts.get(row.fetch_route, 0) + 1
                            if row.target_actor:
                                neighbor_counts[row.target_actor] += 1
                                neighbor_sources[row.target_actor].add(seed.name)
                    except Exception as exc:
                        diagnostics.failed_seeds[seed.name] = str(exc)
            finally:
                close_browser()

        diagnostics.discovered_neighbors = [
            DiscoveredNeighbor(
                handle=handle,
                mention_count=count,
                discovered_from=sorted(neighbor_sources[handle]),
            )
            for handle, count in neighbor_counts.items()
            if count >= self.config.neighbor_frequency_threshold
        ]
        return records, diagnostics

    def _open_browser(self, playwright, diagnostics: ObservationDiagnostics):
        if self.config.cdp_url:
            try:
                browser = playwright.chromium.connect_over_cdp(self.config.cdp_url)
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                diagnostics.notes.append(f"已通过 CDP 连接浏览器：{self.config.cdp_url}")
                return browser, context.new_page, browser.close
            except Exception as exc:
                diagnostics.notes.append(f"CDP 连接失败：{exc}")
                diagnostics.failed_seeds["__browser__"] = "cdp_connect_failed"
                return None, None, lambda: None
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=self.config.user_data_dir,
                channel=self.config.browser_channel or None,
                headless=self.config.headless,
            )
            return context, context.new_page, context.close
        except Exception as exc:
            message = str(exc)
            retry = self._retry_without_channel(playwright, diagnostics, message)
            if retry[0] is not None:
                return retry
            if "ProcessSingleton" in message or "SingletonLock" in message:
                diagnostics.notes.append(
                    "浏览器 profile 正被其他 Chrome/Chromium 进程占用。当前建议改用 X_BROWSER_CDP_URL 连接已打开的 Chrome。"
                )
                diagnostics.failed_seeds["__browser__"] = "profile_locked"
                return None, None, lambda: None
            if "Failed to decrypt token" in message or "token_service_table" in message:
                diagnostics.notes.append(
                    "当前浏览器进程无法解密现有 Chrome profile 的登录令牌。建议改用 CDP 模式连接已打开的 Chrome。"
                )
                diagnostics.failed_seeds["__browser__"] = "token_decrypt_failed"
                return None, None, lambda: None
            diagnostics.notes.append(f"浏览器启动失败：{message}")
            diagnostics.failed_seeds["__browser__"] = "launch_failed"
            return None, None, lambda: None

    def _retry_without_channel(self, playwright, diagnostics: ObservationDiagnostics, message: str):
        retryable_patterns = [
            "Crashpad/settings.dat",
            "Operation not permitted",
            "Permission denied",
            "SIGABRT",
        ]
        if not self.config.browser_channel:
            return None, None, lambda: None
        if not any(pattern in message for pattern in retryable_patterns):
            return None, None, lambda: None
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=self.config.user_data_dir,
                channel=None,
                headless=self.config.headless,
            )
            diagnostics.notes.append(
                "系统 Chrome 通道在当前环境下启动失败，已自动回退到 Playwright Chromium。"
            )
            return context, context.new_page, context.close
        except Exception:
            return None, None, lambda: None

    def _observe_seed(
        self,
        page,
        seed: SeedPerson,
        cutoff: datetime,
    ) -> tuple[list[ObservedTweet], list[SeedViewDiagnostic]]:
        handle = seed.twitter_handle.strip().lstrip("@")
        rows: list[ObservedTweet] = []
        diagnostics: list[SeedViewDiagnostic] = []
        seen_urls: set[str] = set()
        route_adapters = build_route_adapters()
        tweet_post_has_recent_signal = False
        for adapter in route_adapters:
            if adapter.raw_type not in self.config.behavior_types:
                continue
            if adapter.is_search_fallback and tweet_post_has_recent_signal:
                continue
            url = adapter.build_url(self.config.base_url, handle, cutoff)
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2500)
            for _ in range(6 if adapter.is_search_fallback else 4):
                page.mouse.wheel(0, 2200)
                page.wait_for_timeout(1200)
            try:
                article_count = page.locator("article").count()
            except Exception:
                article_count = 0
            page_url = page.url
            try:
                page_title = page.title()
            except Exception:
                page_title = ""
            extracted = extract_article_payloads(page, self.config.max_items_per_view * 3)
            extracted_count = 0
            stale_candidate_count = 0
            missing_timestamp_count = 0
            missing_status_link_count = 0
            sample_timestamp = ""
            sample_status_url = ""
            sample_excerpt = ""
            sample_html = ""
            for item in extracted:
                timestamp = item.get("timestamp", "")
                content = (item.get("content") or "").strip()
                if not content:
                    continue
                if not sample_html and item.get("html"):
                    sample_html = item.get("html")
                if not sample_timestamp and timestamp:
                    sample_timestamp = timestamp
                source_url = item.get("source_url", "")
                if not source_url:
                    source_url = first_status_link(item.get("link_candidates", []))
                if not sample_excerpt:
                    sample_excerpt = content[:160].replace("\n", " ")
                if not sample_status_url and source_url:
                    sample_status_url = source_url
                if not timestamp:
                    missing_timestamp_count += 1
                    timestamp = fallback_timestamp()
                event_time = parse_datetime(timestamp)
                if event_time and event_time < cutoff:
                    stale_candidate_count += 1
                    continue
                if not source_url or source_url in seen_urls:
                    if not source_url:
                        missing_status_link_count += 1
                    continue
                seen_urls.add(source_url)
                tags = infer_tags(content, seed)
                target_actor = infer_target_actor(content, source_url, handle)
                inferred_raw_type = adapter.raw_type
                if adapter.raw_type == "tweet_post" and content.lower().startswith("rt @"):
                    inferred_raw_type = "retweet"
                rows.append(
                    ObservedTweet(
                        source="twitter",
                        author=seed.name,
                        content=content,
                        timestamp=timestamp,
                        raw_type=inferred_raw_type,
                        source_url=source_url,
                        observed_via="browser_observer",
                        observed_relationship="seed",
                        fetch_route=adapter.route_key,
                        target_actor=target_actor,
                        metrics=item.get("metrics", {}) or {},
                        tags=tags,
                        seed_key=seed.key,
                    )
                )
                extracted_count += 1
                if adapter.raw_type == "tweet_post":
                    tweet_post_has_recent_signal = True
            diagnostics.append(
                SeedViewDiagnostic(
                    seed_name=seed.name,
                    handle=handle,
                    view_name=adapter.view_name,
                    page_url=page_url,
                    page_title=page_title,
                    article_count=article_count,
                    extracted_count=extracted_count,
                    stale_candidate_count=stale_candidate_count,
                    missing_timestamp_count=missing_timestamp_count,
                    missing_status_link_count=missing_status_link_count,
                    sample_timestamp=sample_timestamp,
                    sample_status_url=sample_status_url,
                    sample_excerpt=sample_excerpt,
                    sample_html=sample_html,
                    note=infer_page_note(
                        page_title=page_title,
                        page_url=page_url,
                        requested_url=url,
                        article_count=article_count,
                        extracted_count=extracted_count,
                        stale_candidate_count=stale_candidate_count,
                        missing_timestamp_count=missing_timestamp_count,
                        missing_status_link_count=missing_status_link_count,
                        is_search_fallback=adapter.is_search_fallback,
                    ),
                )
            )
        return rows, diagnostics


def _load_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    return sync_playwright
