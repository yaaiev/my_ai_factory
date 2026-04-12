# 工作流地图

## 阶段链路

1. `01-discovery`
   目标：确定人物池、数据源、事件定义、合规边界
2. `02-design`
   目标：确定系统架构、数据模型、Agent 拓扑、评分机制
3. `03-implementation`
   目标：搭建 seed 管理、采集、ETL、图谱、输出的最小闭环
4. `04-verification`
   目标：验证采集质量、结构化准确性、预测与评分稳定性
5. `05-delivery`
   目标：输出日报、信号预警、研究 memo、watchlist 影响摘要
6. `06-iteration`
   目标：吸收反馈、补 memory、扩 sources、优化模型

## 阶段依赖

- `02-design` 依赖 `01-discovery` 的人物池与事件范围
- `03-implementation` 依赖 `02-design` 的 schema 与 contracts
- `04-verification` 依赖 `03-implementation` 的最小可运行管线
- `05-delivery` 依赖验证通过的结构化事件和评分产物
- `06-iteration` 依赖交付和验证阶段的证据

## 并行区

- Source catalog 和 seed list 可并行推进
- ETL schema 和 graph schema 可并行设计
- 日报模板与预警规则可在实现前提前定义
