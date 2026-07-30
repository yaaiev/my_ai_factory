"""
相对路径：projects/ai-intel-terminal/twitter_observer/adapters.py
文件说明：Twitter/X 获取路由适配器，参考 OpenCLI 的 adapter 思路拆分不同视图。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote


@dataclass(frozen=True, slots=True)
class TwitterRouteAdapter:
    route_key: str
    raw_type: str
    view_name: str
    description: str
    is_search_fallback: bool = False

    def build_url(self, base_url: str, handle: str, cutoff: datetime) -> str:
        if self.route_key == "profile_timeline":
            return f"{base_url}/{handle}"
        if self.route_key == "reply_view":
            return f"{base_url}/{handle}/with_replies"
        if self.route_key == "likes_view":
            return f"{base_url}/{handle}/likes"
        if self.route_key == "search_recent":
            since = cutoff.date().isoformat()
            query = quote(f"(from:{handle}) since:{since}")
            return f"{base_url}/search?q={query}&src=typed_query&f=live"
        raise ValueError(f"unknown twitter route adapter: {self.route_key}")


def build_route_adapters() -> list[TwitterRouteAdapter]:
    return [
        TwitterRouteAdapter(
            route_key="profile_timeline",
            raw_type="tweet_post",
            view_name="tweet_post",
            description="个人主页时间线，用于补充上下文与公开发帖。",
        ),
        TwitterRouteAdapter(
            route_key="reply_view",
            raw_type="reply",
            view_name="reply",
            description="回复视图，用于捕捉互动、观点澄清与短期异动。",
        ),
        TwitterRouteAdapter(
            route_key="likes_view",
            raw_type="like",
            view_name="like",
            description="点赞视图，用于弱偏好与一度关系观察。",
        ),
        TwitterRouteAdapter(
            route_key="search_recent",
            raw_type="tweet_post",
            view_name="tweet_post_search_recent",
            description="recent search 视图，用于优先命中最近时间窗口内容。",
            is_search_fallback=True,
        ),
    ]
