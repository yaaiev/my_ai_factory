"""
相对路径：projects/ai-intel-terminal/delivery/investment_signal_report.py
文件说明：Twitter/X 信号驱动的投资结论中文报告生成器。
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

from signals.contracts import ScoredSignal


def build_investment_signal_report(
    signals: list[ScoredSignal],
    title: str,
    report_mode: str = "formal",
    diagnostics: dict[str, object] | None = None,
) -> str:
    filtered = filter_reportable_signals(signals, report_mode=report_mode)
    ranked = sorted(filtered, key=lambda item: item.signal_score, reverse=True)
    top_signals = ranked[:5]
    lines = [
        f"# {title}",
        "",
        f"- 生成时间：{datetime.now(timezone.utc).isoformat()}",
        f"- 信号总数：{len(filtered)}",
        f"- 报告模式：{'正式报告' if report_mode == 'formal' else '测试/开发报告'}",
        "",
        "## 今日 5 条投资结论",
        "",
    ]
    if not top_signals:
        lines.append("- 暂无可报告信号。")
        if diagnostics:
            lines.extend(_build_diagnostics_section(diagnostics))
        return "\n".join(lines) + "\n"

    for index, signal in enumerate(top_signals, start=1):
        lines.append(f"{index}. {signal.actor} - {signal.summary}")
        lines.append(f"   - 事实摘要：{build_fact_summary(signal)}")
        lines.append(f"   - 情报意义：{signal.research_reason_zh or '需结合更多来源交叉验证。'}")
        lines.append(f"   - 研究建议：{signal.mapped_action}")
        lines.append(
            f"   - 信号类别：`{signal.signal_class}` | 行为：`{signal.behavior_type}` | Signal Score：`{signal.signal_score:.4f}` | 风险：`{signal.risk_score:.2f}`"
        )
        lines.append(f"   - 投资映射：{signal.mapped_impact}")
        lines.append(
            "   - 评分拆解："
            f" actor=`{signal.actor_weight:.2f}` | behavior=`{signal.behavior_weight:.2f}` |"
            f" propagation=`{signal.propagation_weight:.2f}` | consistency=`{signal.consistency_weight:.2f}`"
        )
        lines.append(f"   - 来源：`{signal.observed_via or 'unknown'}` | 关系：`{signal.observed_relationship}`")
        if signal.fetch_route:
            lines.append(f"   - 获取路径：`{signal.fetch_route}`")
        if signal.target_actor:
            lines.append(f"   - 互动对象：{signal.target_actor}")
        if signal.tags:
            lines.append(f"   - 标签：{', '.join(signal.tags)}")
        if signal.source_link:
            lines.append(f"   - 链接：{signal.source_link}")

    lines.extend(
        [
            "",
            "## 方法说明",
            "",
            "- 当前报告基于行为信号、人物权重、传播强度和一致性进行规则评分。",
            "- 本报告属于 Twitter/X 行为信号层，适合作为前导观察，不应单独替代基本面与多源验证。",
        ]
    )
    if diagnostics:
        lines.extend(_build_diagnostics_section(diagnostics))
    return "\n".join(lines) + "\n"


def filter_reportable_signals(signals: list[ScoredSignal], report_mode: str) -> list[ScoredSignal]:
    if report_mode != "formal":
        return signals
    return [signal for signal in signals if has_real_source_link(signal.source_link)]


def has_real_source_link(link: str) -> bool:
    if not link:
        return False
    parsed = urlparse(link)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.netloc or "").lower()
    return host not in {"example.com", "www.example.com", "localhost"}


def build_fact_summary(signal: ScoredSignal) -> str:
    actor = signal.actor
    if signal.behavior_type == "like":
        target = f"对 {signal.target_actor} 的内容进行了点赞" if signal.target_actor else "对一条外部内容进行了点赞"
        return f"{actor} 在 Twitter/X 上{target}，这代表弱偏好信号，不等同于本人原创公开表态。"
    target = f"，互动对象为 {signal.target_actor}" if signal.target_actor else ""
    return f"{actor} 在 Twitter/X 上出现一条 `{signal.behavior_type}` 行为{target}，当前被系统归类为 `{signal.signal_class}`。"


def _build_diagnostics_section(diagnostics: dict[str, object]) -> list[str]:
    lines = ["", "## 运行诊断", ""]
    for key, value in diagnostics.items():
        lines.append(f"- {key}：{value}")
    return lines
