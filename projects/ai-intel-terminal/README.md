# AI Intel Terminal

一个面向一级/二级市场研究的顶级 AI 情报系统项目。

核心目标是围绕“硅谷 AI Top 50 关键人物”建立持续自动化的情报能力：

- 自动追踪人物、公司、模型、论文和招聘动态
- 将原始信号转换为结构化事件
- 通过知识图谱与时间序列分析发现关联
- 生成趋势预测、预警信号和投资备忘录

## 第一阶段目标

第一阶段不追求全栈产品闭环，而是优先完成可持续演进的工程底座：

- 明确项目级工作流
- 固化数据流和 Agent 分工
- 定义事件结构化 schema
- 定义知识图谱实体与关系
- 搭建 MVP 数据库草案
- 明确风险与验证标准

## 产品分层

1. Top 50 人物种子层
2. 多源互联网扫描层
3. 数据清洗与结构化层
4. AI 理解与预测层
5. 知识图谱层
6. 投资辅助输出层

## 第一版交付范围

- 项目治理骨架
- 路由地图与流程卡
- 系统架构说明
- 数据库 schema 草案
- Agent 拓扑设计
- 风险登记与优先级拆解

## 快速开始

1. 先读 [AGENTS.md](/Users/dev/yana_prj/my_ai_factory/projects/ai-intel-terminal/AGENTS.md)
2. 再读 [docs/routes/00-index.md](/Users/dev/yana_prj/my_ai_factory/projects/ai-intel-terminal/docs/routes/00-index.md)
3. 若开始设计数据层，读 [docs/architecture/02-data-model.md](/Users/dev/yana_prj/my_ai_factory/projects/ai-intel-terminal/docs/architecture/02-data-model.md)
4. 若开始落实现流程，读 [workflow/03-implementation.md](/Users/dev/yana_prj/my_ai_factory/projects/ai-intel-terminal/workflow/03-implementation.md)

## MVP 建议技术栈

- 编排层：Python
- 抓取与调度：RSS/API 优先，必要时补轻量 crawler
- 结构化存储：PostgreSQL 或 SQLite + DuckDB
- 图谱层：第一版先用关系表 + 图视图，后续再评估 Neo4j
- 检索与聚类：Embedding + 向量索引
- LLM 层：事件抽取、摘要、预测、备忘录生成

## 当前成功标准

- 能维护 Top 50 核心人物清单
- 能采集并结构化至少 3 类高信号源
- 能对事件做去重、聚类、分类和打分
- 能输出日报、预警和研究 memo 的草案
