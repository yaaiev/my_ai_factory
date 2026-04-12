# Implementation

## 目标

- 逐步实现 seed 管理、采集、ETL、评分、输出的最小闭环

## 输入

- 已确认的系统设计与 schema

## 输出

- seed registry
- source connectors
- ETL pipeline
- scoring logic
- delivery generators

## 责任角色

- 主责任 Agent：Orchestrator
- 可协作 Agent：Scout Agent、ETL Agent、Intel Analyst Agent、Graph Agent

## 执行动作

1. 先实现 seed 和 source catalog
2. 再实现 raw document ingestion
3. 再实现 event extraction 与 clustering
4. 再实现 scoring、prediction 和 delivery 模板

## 验收标准

1. 至少一条 source -> raw_document -> event -> delivery 的链路打通
2. 事件能关联到 person 或 company
3. 输出层能消费结构化事件，而不是直接消费原始文本

## 失败回退

- 若 ingestion 不稳定，先冻结 source 扩展，集中打通单源闭环

## 下一跳

- `04-verification.md`
