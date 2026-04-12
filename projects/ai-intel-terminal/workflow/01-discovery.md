# Discovery

## 目标

- 明确 Top 50 人物池、优先数据源、事件分类边界与合规边界

## 输入

- 项目目标
- 用户给出的六层系统设计

## 输出

- Top 50 seed schema
- source catalog
- 事件 taxonomy 初稿
- 风险边界初稿

## 责任角色

- 主责任 Agent：Orchestrator
- 可协作 Agent：Scout Agent、Reviewer

## 执行动作

1. 定义人物主数据字段
2. 定义高/中/弱信号源优先级
3. 明确“事件”与“原始文本”的边界
4. 记录合规与访问限制

## 验收标准

1. 人物、source、event 三类基础对象字段明确
2. 至少 3 类高信号源被纳入第一阶段
3. 明确哪些源只做观察，不做第一轮接入

## 失败回退

- 若 source 边界不清，回到范围定义并压缩 MVP

## 下一跳

- `02-design.md`
