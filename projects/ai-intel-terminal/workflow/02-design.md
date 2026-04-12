# Design

## 目标

- 完成架构、数据模型、Agent 拓扑和评分框架设计

## 输入

- discovery 阶段定义的人物池、source catalog 与 taxonomy

## 输出

- 系统架构文档
- 数据模型文档
- Agent 拓扑文档
- schema.sql

## 责任角色

- 主责任 Agent：Orchestrator
- 可协作 Agent：ETL Agent、Intel Analyst Agent、Graph Agent

## 执行动作

1. 设计 6 层系统边界
2. 设计事实层、推断层、输出层数据合同
3. 设计 Agent handoff 顺序
4. 设计最小验证口径

## 验收标准

1. 每个核心对象都能映射到数据表或结构化输出
2. Agent 分工无明显职责重叠
3. MVP 范围被限制在可实现的最小闭环

## 失败回退

- 若 schema 和产品目标不一致，回到 discovery 重新收敛事件范围

## 下一跳

- `03-implementation.md`
