# 路由索引

## 使用顺序

1. 先读 [01-root-map.md](/Users/dev/yana_prj/my_ai_factory/projects/ai-intel-terminal/docs/routes/01-root-map.md)
2. 再读 [02-workflow-map.md](/Users/dev/yana_prj/my_ai_factory/projects/ai-intel-terminal/docs/routes/02-workflow-map.md)
3. 若要理解系统结构，读 [../architecture/01-system-architecture.md](/Users/dev/yana_prj/my_ai_factory/projects/ai-intel-terminal/docs/architecture/01-system-architecture.md)
4. 若要开始建表和管线，读 [../architecture/02-data-model.md](/Users/dev/yana_prj/my_ai_factory/projects/ai-intel-terminal/docs/architecture/02-data-model.md)

## 路由原则

- 先判当前处在“发现、设计、实现、验证、交付、迭代”的哪一步。
- 只加载当前阶段需要的最小文档，不全量阅读。
- 每一轮实现都必须绑定到 6 层系统中的至少一层。

## 常见起点

- 定义数据源与人物池：`workflow/01-discovery.md`
- 定义 schema 和图谱：`docs/architecture/02-data-model.md`
- 定义 Agent 协作方式：`docs/architecture/03-agent-topology.md`
- 开始 MVP 编码：`workflow/03-implementation.md`
