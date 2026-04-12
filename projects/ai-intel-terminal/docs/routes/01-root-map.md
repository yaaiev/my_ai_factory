# 根地图

## 根目录结构

- `AGENTS.md`：常驻事实、入口与硬约束
- `README.md`：项目目标与快速开始
- `memory-topic-registry.md`：长期知识主题边界
- `docs/routes/`：导航入口
- `docs/architecture/`：系统、数据、Agent 设计
- `workflow/`：阶段卡片
- `evidence/`：过程证据与实验记录
- `data/`：schema、seed、样例工件

## 推荐工作起点

- 如果要定义 Top 50 人物池，从 `workflow/01-discovery.md` 开始
- 如果要建 ETL/数据库，从 `docs/architecture/02-data-model.md` 开始
- 如果要搭多 Agent 协作，从 `docs/architecture/03-agent-topology.md` 开始
- 如果要产出日报/预警/memo，从 `workflow/05-delivery.md` 开始

## 核心产物关系

- `workflow/` 定义阶段动作
- `docs/architecture/` 定义结构约束
- `data/` 定义数据合同
- `evidence/` 保留真实执行痕迹
