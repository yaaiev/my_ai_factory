# Iteration

## 目标

- 根据真实使用反馈持续扩展 source、优化评分、修正 topic 组织

## 输入

- 验证结果
- 交付结果
- 用户反馈

## 输出

- 优先级 backlog
- memory 更新建议
- source 扩展计划

## 责任角色

- 主责任 Agent：Orchestrator
- 可协作 Agent：Reviewer、全部功能 Agent

## 执行动作

1. 汇总本轮失败点和强信号点
2. 更新 memory topic 和风险清单
3. 确定下轮只做最重要的一条能力链

## 验收标准

1. 至少形成一个可执行的下一轮目标
2. 新增 source 不破坏现有闭环
3. 经验被沉淀到 memory 或 evidence

## 失败回退

- 若 backlog 过于发散，回退到 discovery 重排目标边界

## 下一跳

- `01-discovery.md`
