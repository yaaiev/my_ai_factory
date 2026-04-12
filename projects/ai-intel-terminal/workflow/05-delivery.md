# Delivery

## 目标

- 产出可被研究员直接消费的日报、预警和研究 memo

## 输入

- 已验证通过的结构化事件、cluster 和 prediction

## 输出

- 每日情报日报
- 信号预警
- 研究 memo
- watchlist 影响摘要

## 责任角色

- 主责任 Agent：Intel Analyst Agent
- 可协作 Agent：Orchestrator、Reviewer

## 执行动作

1. 对事件按 relevance 和 signal strength 排序
2. 生成分层输出
3. 标注事实、推断和风险说明
4. 记录交付日期与 source scope

## 验收标准

1. 输出能说明“发生了什么、为什么重要、影响谁”
2. 所有结论可追溯到事件或 cluster
3. 报告不是原文拼接，而是结构化总结

## 失败回退

- 若输出不稳定，回退到 verification 修正评分与模板

## 下一跳

- `06-iteration.md`
