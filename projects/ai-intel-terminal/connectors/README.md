# Connectors

本目录承接采集层的统一接口。

## 设计原则

- 每个 source connector 都必须输出统一的原始文档结构
- connector 负责采集与最小标准化，不负责复杂推理
- 复杂分类、去重、聚类由 ETL 层负责
- 浏览器驱动型 connector 只作为补充，不作为第一阶段默认方案

## 统一职责

- `fetch_raw()`
- `normalize_document()`
- `healthcheck()`

## 第一阶段实现顺序

1. `rss_news.py`
2. `github_activity.py`
3. `browser_backed_x.py` 仅保留扩展口，不立即实现

## Plan -> Build -> Evaluate -> Iterate 在本目录中的落点

- Plan：为每个 source 明确 contract、频率、字段与失败策略
- Build：只实现一条最小 source -> raw_document 链路
- Evaluate：检查成功率、噪声、稳定性和结构化质量
- Iterate：决定扩展、降级或淘汰该 connector
