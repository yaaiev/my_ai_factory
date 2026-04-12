# AGENTS.md

## 项目定位

- 本项目是一个“AI 行业情报终端”，目标是围绕硅谷 AI Top 50 关键人物构建持续追踪、结构化分析和投资辅助决策能力。
- 当前优先级是先完成可运行的情报底座，再逐步扩展到更深的预测与图谱能力。
- 默认采用 `memory-first + route-first` 组织方式。

## 默认读取顺序

1. 本文件
2. [memory-topic-registry.md](/Users/dev/yana_prj/my_ai_factory/projects/ai-intel-terminal/memory-topic-registry.md)
3. [docs/routes/00-index.md](/Users/dev/yana_prj/my_ai_factory/projects/ai-intel-terminal/docs/routes/00-index.md)
4. `evidence/`
5. 相关 `docs/architecture/`

## 工作流入口

- 需求拆解与范围确认：`workflow/01-discovery.md`
- 架构与模型设计：`workflow/02-design.md`
- 编码与集成：`workflow/03-implementation.md`
- 验证与评估：`workflow/04-verification.md`
- 输出产品与交付：`workflow/05-delivery.md`
- 情报回顾与迭代：`workflow/06-iteration.md`

## 常驻事实

- 研究对象不是“全网 AI”，而是“关键人物驱动的 AI 情报网络”。
- 采集目标不是网页，而是可落到时间线中的“事件”。
- 第一版高信号源优先级：`X/Twitter`、新闻/RSS、GitHub、YouTube/播客 transcript。
- 第一版图谱实现优先选择轻量方案，避免过早引入重图数据库。

## 关键角色

- `Orchestrator`：跨流程调度、优先级控制、决策升级。
- `Scout Agent`：采集源管理、抓取策略、源健康检查。
- `ETL Agent`：去重、清洗、NER、RE、聚类、标准化。
- `Intel Analyst Agent`：事件分类、风险评估、趋势预测、memo 草拟。
- `Graph Agent`：实体对齐、关系维护、图谱视图更新。
- `Reviewer`：验收数据质量、模型输出质量和投资可用性。

## 高频硬约束

- 所有采集源必须标注可用性、时效性和合规边界。
- 预测类输出必须显式区分“事实”“推断”“假设”。
- 事件去重、实体对齐和时间归一化必须早于趋势分析。
- 未经验证的传闻不得直接进入高置信度投资信号层。
- 每轮实现都必须说明新增能力对应哪一层系统。

## 实现边界

- MVP 阶段优先做数据合同、流程卡、schema 和可验证的最小管线。
- 暂不在第一轮引入复杂前端仪表盘。
- 暂不在第一轮接入高成本、低稳定性的全网爬虫。

## 验收原则

- 任何新模块都要能指向明确输入、输出、 owner 和验证方式。
- 任何新数据表都要能回答：服务哪层能力、如何更新、如何回溯。
- 任何 Agent 产物都要能被下游阶段直接消费，而不是停留在自由文本。
