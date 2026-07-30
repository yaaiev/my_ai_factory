"""
相对路径：projects/ai-intel-terminal/delivery/unified_investment_brief.py
文件说明：多源统一投资结论报告生成器。
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from delivery.daily_brief import (
    EVENT_TYPE_LABELS_ZH,
    build_chinese_event_brief,
    filter_reportable_events,
    has_real_source_link,
)
from etl.contracts import StructuredEvent
from signals.contracts import ScoredSignal


def build_unified_investment_brief(
    rss_events: list[StructuredEvent],
    github_events: list[StructuredEvent],
    twitter_signals: list[ScoredSignal],
    title: str,
    report_mode: str = "formal",
) -> str:
    ranked_items = rank_items(rss_events, github_events, twitter_signals, report_mode=report_mode)
    lines = [
        f"# {title}",
        "",
        f"- 生成时间：{datetime.now(timezone.utc).isoformat()}",
        f"- RSS 事件数：{len(rss_events)}",
        f"- GitHub 事件数：{len(github_events)}",
        f"- Twitter/X 信号数：{len(twitter_signals)}",
        f"- 报告模式：{'正式报告' if report_mode == 'formal' else '测试/开发报告'}",
        "",
        "## 今日最强 5 条投资结论",
        "",
    ]
    if not ranked_items:
        lines.append("- 暂无可汇总的有效结论。")
    for index, item in enumerate(ranked_items[:5], start=1):
        lines.append(f"{index}. {item['headline']}")
        lines.append(f"   - 事实摘要：{item['fact_summary']}")
        lines.append(f"   - 情报意义：{item['intel_meaning']}")
        lines.append(f"   - 研究建议：{item['research_action']}")
        lines.append(
            f"   - 来源：`{item['source']}` | 类别：`{item['category']}` | 强度：`{item['score']:.2f}` | 风险：`{item['risk']:.2f}`"
        )
        lines.append(f"   - 链接：{item['link']}")

    lines.extend(["", "## 今日趋势", ""])
    for trend in build_trend_lines(rss_events, github_events, twitter_signals):
        lines.append(f"- {trend}")

    lines.extend(["", "## 今日风险", ""])
    for risk_line in build_risk_lines(rss_events, twitter_signals):
        lines.append(f"- {risk_line}")

    lines.extend(["", "## 今日行动建议", ""])
    for action_line in build_action_lines(ranked_items[:5]):
        lines.append(f"- {action_line}")

    return "\n".join(lines) + "\n"


def rank_items(
    rss_events: list[StructuredEvent],
    github_events: list[StructuredEvent],
    twitter_signals: list[ScoredSignal],
    report_mode: str,
) -> list[dict[str, object]]:
    if report_mode == "formal":
        rss_events = filter_reportable_events(rss_events, report_mode="formal")
        github_events = filter_reportable_events(github_events, report_mode="formal")
    items: list[dict[str, object]] = []
    for signal in twitter_signals:
        if report_mode == "formal" and not has_real_source_link(signal.source_link):
            continue
        items.append(
            {
                "source": "twitter",
                "source_priority": 3,
                "headline": f"{signal.actor} - {signal.summary}",
                "fact_summary": f"{signal.actor} 在 Twitter/X 上出现 `{signal.behavior_type}` 行为，当前被系统识别为 `{signal.signal_class}`。",
                "intel_meaning": signal.research_reason_zh or signal.mapped_impact,
                "research_action": signal.mapped_action,
                "category": signal.signal_class,
                "score": signal.signal_score,
                "risk": signal.risk_score,
                "link": signal.source_link,
            }
        )
    for source_name, source_priority, events, bonus in (
        ("rss", 2, rss_events, 0.08),
        ("github", 1, github_events, 0.0),
    ):
        for event in events:
            if report_mode == "formal" and not has_real_source_link(event.link):
                continue
            fact_summary, intel_meaning, research_action = build_chinese_event_brief(event)
            items.append(
                {
                    "source": source_name,
                    "source_priority": source_priority,
                    "headline": f"{event.person + ' - ' if event.person else ''}{event.summary}",
                    "fact_summary": fact_summary,
                    "intel_meaning": intel_meaning,
                    "research_action": research_action,
                    "category": EVENT_TYPE_LABELS_ZH.get(event.event_type, event.event_type),
                    "score": event.signal_strength_score + event.relevance_score + bonus,
                    "risk": event.risk_score,
                    "link": event.link,
                }
            )
    return sorted(items, key=lambda item: (item["source_priority"], item["score"], -item["risk"]), reverse=True)


def build_trend_lines(
    rss_events: list[StructuredEvent],
    github_events: list[StructuredEvent],
    twitter_signals: list[ScoredSignal],
) -> list[str]:
    event_counter = Counter(event.event_type for event in rss_events + github_events)
    signal_counter = Counter(signal.signal_class for signal in twitter_signals)
    trends = []
    for label, count in signal_counter.most_common(2):
        trends.append(f"Twitter/X 行为信号中 `{label}` 出现 {count} 次，说明该主题正在升温。")
    for label, count in event_counter.most_common(2):
        trends.append(f"RSS/GitHub 事件中 `{EVENT_TYPE_LABELS_ZH.get(label, label)}` 出现 {count} 次，可作为多源验证。")
    return trends or ["当前还没有足够的多源趋势信号。"]


def build_risk_lines(rss_events: list[StructuredEvent], twitter_signals: list[ScoredSignal]) -> list[str]:
    risks = []
    high_risk_signals = [signal for signal in twitter_signals if signal.risk_score >= 0.55]
    if high_risk_signals:
        top = high_risk_signals[0]
        risks.append(f"{top.actor} 的 `{top.signal_class}` 信号风险分较高，需核验是否会外溢到监管或组织层面。")
    media_events = [event for event in rss_events if event.event_type in {"media_reputation", "personal_incident"}]
    if media_events:
        risks.append("今日存在舆情或人物事件，短期内不应直接等同于公司基本面变化。")
    return risks or ["当前高风险信号有限，但仍需持续跟踪正式来源。"]


def build_action_lines(top_items: list[dict[str, object]]) -> list[str]:
    actions = []
    for item in top_items[:3]:
        actions.append(f"优先回看 `{item['source']}` 来源中的原始链接，验证 `{item['category']}` 是否获得第二来源确认。")
    return actions or ["暂无明确行动建议。"]
