"""
相对路径：projects/ai-intel-terminal/delivery/daily_brief.py
文件说明：第一版日报 artifact 生成器。
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

from etl.clustering import EventCluster
from etl.contracts import StructuredEvent

EVENT_TYPE_LABELS_ZH = {
    "model_release": "模型发布",
    "product_iteration": "产品迭代",
    "funding_round": "融资事件",
    "partnership": "合作关系",
    "talent_movement": "人才流动",
    "policy_statement": "政策表态",
    "research_breakthrough": "研究突破",
    "infra_expansion": "基础设施扩张",
    "media_reputation": "舆情事件",
    "personal_incident": "人物事件",
    "rumor": "传闻",
}


def build_daily_brief(
    events: list[StructuredEvent],
    clusters: list[EventCluster],
    title: str = "AI Intel Daily Brief",
    language: str = "zh",
    report_mode: str = "formal",
) -> str:
    filtered_events = filter_reportable_events(events, report_mode=report_mode)
    filtered_clusters = filter_clusters_for_events(
        clusters=clusters,
        original_events=events,
        filtered_events=filtered_events,
    )
    if language == "zh":
        return build_daily_brief_zh(
            events=filtered_events,
            clusters=filtered_clusters,
            title=title,
            report_mode=report_mode,
        )
    return build_daily_brief_en(
        events=filtered_events,
        clusters=filtered_clusters,
        title=title,
        report_mode=report_mode,
    )


def build_daily_brief_zh(
    events: list[StructuredEvent],
    clusters: list[EventCluster],
    title: str,
    report_mode: str,
) -> str:
    sorted_events = sorted(
        events,
        key=lambda event: (event.relevance_score, event.risk_score, event.timestamp),
        reverse=True,
    )
    top_events = sorted_events[:6]
    lines = [
        f"# {title}",
        "",
        f"- 生成时间：{datetime.now(timezone.utc).isoformat()}",
        f"- 事件数：{len(events)}",
        f"- 聚类数：{len(clusters)}",
        f"- 报告模式：{'正式报告' if report_mode == 'formal' else '测试/开发报告'}",
        "",
        "## 今日最重要的动态",
        "",
    ]
    if not top_events:
        lines.append("- 暂无事件。")
    for index, event in enumerate(top_events, start=1):
        person_prefix = f"{event.person} - " if event.person else ""
        lines.append(
            f"{index}. {person_prefix}{event.summary}"
        )
        fact_summary, intel_meaning, research_action = build_chinese_event_brief(event)
        lines.append(f"   - 事实摘要：{fact_summary}")
        lines.append(f"   - 情报意义：{intel_meaning}")
        lines.append(f"   - 研究建议：{research_action}")
        lines.append(
            f"   - 类型：`{EVENT_TYPE_LABELS_ZH.get(event.event_type, event.event_type)}` | 平台：`{event.platform}` | 相关度：`{event.relevance_score:.2f}` | 风险：`{event.risk_score:.2f}`"
        )
        if event.matched_person_keys:
            lines.append(f"   - 匹配人物：{', '.join(event.matched_person_keys)}")
        if event.entities:
            lines.append(f"   - 相关实体：{', '.join(event.entities)}")
        lines.append(f"   - 链接：{event.link}")

    lines.extend(
        [
            "",
            "## 聚类摘要",
            "",
        ]
    )
    if not clusters:
        lines.append("- 暂无聚类。")
    for cluster in clusters[:6]:
        lines.append(
            f"- {cluster.cluster_summary} | cluster=`{cluster.cluster_key[:12]}` | 事件数=`{len(cluster.event_indexes)}` | 置信度=`{cluster.confidence_score:.2f}`"
        )

    lines.extend(
        [
            "",
            "## 初步观察",
            "",
            "- 本日报为规则与 seed 驱动的 MVP 产物，尚未接入完整 LLM 推理层。",
            "- 所有结论都应回溯到 source document、event 和 cluster 后再用于研究判断。",
        ]
    )
    if report_mode == "formal":
        lines.append("- 本正式报告仅展示包含真实 http/https 来源链接的事件。")
    else:
        lines.append("- 本文件属于测试/开发验证产物，可能包含 fixture 或 mock 数据，不应用于正式研究判断。")
    return "\n".join(lines) + "\n"


def build_daily_brief_en(
    events: list[StructuredEvent],
    clusters: list[EventCluster],
    title: str,
    report_mode: str,
) -> str:
    sorted_events = sorted(
        events,
        key=lambda event: (event.relevance_score, event.risk_score, event.timestamp),
        reverse=True,
    )
    top_events = sorted_events[:6]
    lines = [
        f"# {title}",
        "",
        f"- Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"- Events: {len(events)}",
        f"- Clusters: {len(clusters)}",
        f"- Report mode: {'formal' if report_mode == 'formal' else 'test'}",
        "",
        "## Top Developments",
        "",
    ]
    if not top_events:
        lines.append("- No events.")
    for index, event in enumerate(top_events, start=1):
        person_prefix = f"{event.person} - " if event.person else ""
        lines.append(f"{index}. {person_prefix}{event.summary}")
        lines.append(
            f"   - Type: `{event.event_type}` | Platform: `{event.platform}` | Relevance: `{event.relevance_score:.2f}` | Risk: `{event.risk_score:.2f}`"
        )
        if event.matched_person_keys:
            lines.append(f"   - Matched people: {', '.join(event.matched_person_keys)}")
        if event.entities:
            lines.append(f"   - Entities: {', '.join(event.entities)}")
        lines.append(f"   - Link: {event.link}")

    lines.extend(["", "## Cluster Summary", ""])
    if not clusters:
        lines.append("- No clusters.")
    for cluster in clusters[:6]:
        lines.append(
            f"- {cluster.cluster_summary} | cluster=`{cluster.cluster_key[:12]}` | events=`{len(cluster.event_indexes)}` | confidence=`{cluster.confidence_score:.2f}`"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This brief is generated by the current rule-and-seed MVP pipeline.",
            "- Every conclusion should be traced back to source documents, events, and clusters before research use.",
        ]
    )
    if report_mode == "formal":
        lines.append("- This formal brief only includes events with real http/https source links.")
    else:
        lines.append("- This is a test/development artifact and may contain fixture or mock data.")
    return "\n".join(lines) + "\n"


def filter_reportable_events(
    events: list[StructuredEvent],
    report_mode: str,
) -> list[StructuredEvent]:
    if report_mode != "formal":
        return events
    return [
        event
        for event in events
        if has_real_source_link(event.link) and not is_low_signal_promotional_event(event)
    ]


def filter_clusters_for_events(
    clusters: list[EventCluster],
    original_events: list[StructuredEvent],
    filtered_events: list[StructuredEvent],
) -> list[EventCluster]:
    allowed_event_ids = {id(event) for event in filtered_events}
    filtered: list[EventCluster] = []
    for cluster in clusters:
        event_indexes = [
            index
            for index in cluster.event_indexes
            if 0 <= index < len(original_events) and id(original_events[index]) in allowed_event_ids
        ]
        if not event_indexes:
            continue
        filtered.append(
            EventCluster(
                cluster_key=cluster.cluster_key,
                cluster_summary=cluster.cluster_summary,
                canonical_event_index=(
                    cluster.canonical_event_index
                    if 0 <= cluster.canonical_event_index < len(original_events)
                    and id(original_events[cluster.canonical_event_index]) in allowed_event_ids
                    else event_indexes[0]
                ),
                event_indexes=event_indexes,
                confidence_score=cluster.confidence_score,
                first_seen_at=cluster.first_seen_at,
                last_seen_at=cluster.last_seen_at,
            )
        )
    return filtered


def has_real_source_link(link: str) -> bool:
    if not link:
        return False
    parsed = urlparse(link)
    if parsed.scheme not in {"http", "https"}:
        return False
    hostname = (parsed.netloc or "").lower()
    if not hostname:
        return False
    blocked_hosts = {"example.com", "www.example.com", "localhost"}
    return hostname not in blocked_hosts


def build_chinese_event_brief(event: StructuredEvent) -> tuple[str, str, str]:
    subject = event.person or infer_subject(event)
    event_label = EVENT_TYPE_LABELS_ZH.get(event.event_type, event.event_type)

    if event.event_type == "personal_incident":
        fact_summary = f"{subject} 针对一条人物或舆情相关事件做出公开回应，当前焦点更偏个人层面而非业务发布。"
        intel_meaning = "这类动态通常反映舆情、声誉或个人安全层面的波动，暂时不应直接解读为公司战略或模型进展。"
        research_action = "建议回看原报道、当事人回应与公司正式表态，确认是否进一步外溢到组织层面。"
        return fact_summary, intel_meaning, research_action

    if event.event_type == "media_reputation":
        fact_summary = f"{subject} 出现一条与舆情、争议或外部评价相关的动态。"
        intel_meaning = "这类事件更适合作为声誉与传播观察信号，而不是直接投资主信号。"
        research_action = "建议核验争议来源、传播范围及是否出现后续政策或平台动作。"
        return fact_summary, intel_meaning, research_action

    if event.event_type == "model_release":
        fact_summary = f"{subject} 出现一条与产品、模型发布或功能上线相关的动态。"
        intel_meaning = "这类事件通常对应产品节奏、商业化进展或生态动作，值得纳入核心观察清单。"
        research_action = "建议继续核验发布时间、覆盖范围、配套定价和生态反馈。"
        return fact_summary, intel_meaning, research_action

    if event.event_type == "product_iteration":
        fact_summary = f"{subject} 出现一条与 API、SDK、版本发布或产品能力迭代相关的动态。"
        intel_meaning = "这类事件通常反映开发者生态成熟度、产品细节完善和商业可用性提升。"
        research_action = "建议继续核验版本说明、接口能力变化和开发者社区反馈。"
        return fact_summary, intel_meaning, research_action

    if event.event_type == "talent_movement":
        fact_summary = f"{subject} 相关动态显示团队扩招、加入或组织变动信号。"
        intel_meaning = "这类事件通常能反映资源倾斜方向、组织重点和未来能力建设。"
        research_action = "建议结合招聘页面、组织公告和相关人物动态，确认是否为持续性动作。"
        return fact_summary, intel_meaning, research_action

    if event.event_type == "infra_expansion":
        fact_summary = f"{subject} 相关动态显示基础设施、部署能力或算力扩张信号。"
        intel_meaning = "这通常意味着更大规模的产品交付、训练或推理资源投入。"
        research_action = "建议结合 GPU、部署、数据中心和招聘信息交叉验证。"
        return fact_summary, intel_meaning, research_action

    if event.event_type == "funding_round":
        fact_summary = f"{subject} 相关动态指向资本、融资或投资层面的新进展。"
        intel_meaning = "这类事件通常直接影响竞争格局、资源获取能力和估值叙事。"
        research_action = "建议核验金额、投资方、交易结构及潜在产业协同。"
        return fact_summary, intel_meaning, research_action

    if event.event_type == "policy_statement":
        fact_summary = f"{subject} 相关动态涉及政策、监管或公开立场表达。"
        intel_meaning = "这类事件会影响行业边界、合规要求和长期商业环境。"
        research_action = "建议结合监管文本、听证会记录和公司后续动作做持续跟踪。"
        return fact_summary, intel_meaning, research_action

    fact_summary = f"{subject} 出现一条被当前系统归类为{event_label}的动态。"
    intel_meaning = "这条资讯具备一定观察价值，但现阶段分类仍基于规则，需结合原始内容做人工判断。"
    research_action = "建议打开原始链接核验核心事实，再决定是否纳入高优先级研究。"
    return fact_summary, intel_meaning, research_action


def infer_subject(event: StructuredEvent) -> str:
    if event.entities:
        return "、".join(event.entities[:2])
    title = event.summary.strip()
    if " - " in title:
        return title.split(" - ", 1)[0].strip() or "该资讯"
    words = title.split()
    if len(words) >= 2:
        return " ".join(words[:2])
    return title or "该资讯"


def is_low_signal_promotional_event(event: StructuredEvent) -> bool:
    text = f"{event.summary} {event.raw_text}".lower()
    blocked_patterns = [
        "save up to",
        "ticket",
        "disrupt 2026",
        "startup battlefield",
        "heading to tokyo",
        "register now",
        "last chance",
    ]
    return any(pattern in text for pattern in blocked_patterns)
